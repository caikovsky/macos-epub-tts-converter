import argparse
import os
import sys
import tempfile

from audio_handler import process_chapters
from epub_handler import epub_to_chunks
from validation import (
    ValidationError,
    validate_epub_file,
    validate_output_path,
    validate_voice,
    validate_jobs,
    validate_format,
    check_system_dependencies,
    create_safe_output_directory,
)
from logging_config import main_logger, log_system_info, log_exception
from config import config, ConfigError


def main() -> None:
    # Set up logging and log system information
    logger = main_logger
    log_system_info(logger)
    
    # Load configuration and validate
    try:
        config.validate_config()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Get defaults from configuration
    config_defaults = config.get_defaults_for_cli()
    
    parser = argparse.ArgumentParser(
        description="Convert an EPUB file to an audio file using parallel processing.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-i", "--input", help="Path to the input EPUB file."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Base filename for the output audio file (e.g., 'MyBook.mp3').",
    )
    parser.add_argument(
        "-v", "--voice", 
        default=config_defaults.get('voice'),
        help="The voice for speech synthesis (e.g., 'Samantha'). Default from config."
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=config_defaults.get('jobs'),
        help="Number of parallel jobs. Defaults to config setting or (CPU cores - 1).",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["aiff", "mp3"],
        default=config_defaults.get('format', 'aiff'),
        help=f"The output audio format. 'mp3' requires ffmpeg. (default: {config_defaults.get('format', 'aiff')})",
    )
    
    # Update the keep_chapters argument to use config default
    keep_chapters_default = config_defaults.get('keep_chapters', False)
    if keep_chapters_default:
        parser.add_argument(
            "--keep-chapters",
            action="store_true",
            default=True,
            help="Save individual chapter audio files in a dedicated folder. (default: enabled in config)",
        )
        parser.add_argument(
            "--no-keep-chapters",
            action="store_false",
            dest="keep_chapters",
            help="Don't save individual chapter files (override config default).",
        )
    else:
        parser.add_argument(
            "--keep-chapters",
            action="store_true",
            help="If specified, saves the individual chapter audio files in a dedicated folder.",
        )

    # Add configuration-related arguments
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a default config.ini file and exit.",
    )
    parser.add_argument(
        "--config-file",
        help="Path to configuration file (default: config.ini).",
    )

    args = parser.parse_args()
    
    # Handle configuration file creation
    if args.create_config:
        try:
            config.create_default_config_file(force=True)
            logger.info(f"Configuration file created: {config.config_file}")
            print(f"Configuration file created: {config.config_file}")
            print("Edit this file to customize your default settings.")
            sys.exit(0)
        except ConfigError as e:
            logger.error(f"Failed to create config file: {e}")
            print(f"Failed to create config file: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Validate required arguments for normal operation
    if not args.input:
        logger.error("Input EPUB file is required")
        print("Error: Input EPUB file is required (use -i/--input)", file=sys.stderr)
        sys.exit(1)
    if not args.output:
        logger.error("Output filename is required")
        print("Error: Output filename is required (use -o/--output)", file=sys.stderr)
        sys.exit(1)
    
    # If custom config file specified, reload configuration
    if args.config_file:
        try:
            from config import TtsConfig
            # Create a new config instance with the specified file
            custom_config = TtsConfig(args.config_file)
            custom_config.validate_config()
            # Update the global config reference
            import config as config_module
            config_module.config = custom_config
            logger.info(f"Using custom configuration file: {args.config_file}")
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            print(f"Configuration error: {e}", file=sys.stderr)
            sys.exit(1)

    logger.info(f"Starting TTS conversion process")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Voice: {args.voice or 'system default'}")
    logger.info(f"Jobs: {args.jobs or 'auto'}")
    logger.info(f"Format: {args.format}")
    logger.info(f"Keep chapters: {args.keep_chapters}")

    # Validate system dependencies first
    logger.info("Validating system dependencies...")
    deps_valid, deps_error = check_system_dependencies()
    if not deps_valid:
        logger.error(f"System dependency check failed: {deps_error}")
        sys.exit(1)
    logger.info("System dependencies validated successfully")

    # Validate input arguments
    logger.info("Validating input arguments...")
    
    epub_valid, epub_error = validate_epub_file(args.input)
    if not epub_valid:
        logger.error(f"EPUB validation failed: {epub_error}")
        sys.exit(1)
    logger.debug("EPUB file validation passed")

    output_valid, output_path_or_error = validate_output_path(args.output)
    if not output_valid:
        logger.error(f"Output path validation failed: {output_path_or_error}")
        sys.exit(1)
    logger.debug("Output path validation passed")
    
    voice_valid, voice_error = validate_voice(args.voice)
    if not voice_valid:
        logger.error(f"Voice validation failed: {voice_error}")
        sys.exit(1)
    logger.debug("Voice validation passed")

    jobs_valid, jobs_error = validate_jobs(args.jobs)
    if not jobs_valid:
        logger.error(f"Jobs validation failed: {jobs_error}")
        sys.exit(1)
    logger.debug("Jobs validation passed")

    format_valid, format_error = validate_format(args.format)
    if not format_valid:
        logger.error(f"Format validation failed: {format_error}")
        sys.exit(1)
    logger.debug("Format validation passed")

    # Use validated output path
    args.output = output_path_or_error

    # --- Configuration-based Output Directory Logic ---
    logger.info("Creating output directory structure...")
    output_base_name = os.path.splitext(os.path.basename(args.output))[0]
    output_dir = config.get_output_directory()
    try:
        book_output_dir = create_safe_output_directory(output_base_name, output_dir)
        final_output_path = os.path.join(book_output_dir, os.path.basename(args.output))
        logger.info(f"Output directory created: {book_output_dir}")
        logger.info(f"Final output path: {final_output_path}")
    except ValidationError as e:
        logger.error(f"Failed to create output directory: {e}")
        sys.exit(1)
    # --- End Configuration Logic ---

    logger.info("Parsing EPUB file...")
    try:
        title, text_chunks = epub_to_chunks(args.input)
    except Exception as e:
        log_exception(logger, e, "parsing EPUB file")
        sys.exit(1)

    if not text_chunks:
        logger.error("No text content could be extracted from the EPUB")
        sys.exit(1)

    num_chunks = len(text_chunks)
    logger.info(f"Book '{title}' split into {num_chunks} chapters/chunks")

    if args.keep_chapters:
        chapter_suffix = config.get_chapter_suffix()
        chapter_dir = os.path.join(book_output_dir, f"{output_base_name}{chapter_suffix}")
        os.makedirs(chapter_dir, exist_ok=True)

        # --- Pre-run Cleanup Logic (if enabled in config) ---
        if config.should_cleanup_old_files():
            logger.info(f"Cleaning up old chapter files in {chapter_dir}...")
            cleanup_count = 0
            for old_file in os.listdir(chapter_dir):
                if old_file.endswith(".aiff"):
                    os.remove(os.path.join(chapter_dir, old_file))
                    cleanup_count += 1
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} old chapter files")
        # --- End Cleanup Logic ---

        logger.info(f"Chapter files will be saved in: {chapter_dir}")
        try:
            process_chapters(text_chunks, chapter_dir, args, final_output_path)
        except RuntimeError as e:
            logger.error(f"Audio processing failed: {e}")
            sys.exit(1)
        except Exception as e:
            log_exception(logger, e, "processing chapters")
            sys.exit(1)
    else:
        logger.info("Using temporary directory for chapter processing")
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                process_chapters(text_chunks, temp_dir, args, final_output_path)
            except RuntimeError as e:
                logger.error(f"Audio processing failed: {e}")
                sys.exit(1)
            except Exception as e:
                log_exception(logger, e, "processing chapters")
                sys.exit(1)
    
    logger.info("TTS conversion completed successfully!")


if __name__ == "__main__":
    main()
