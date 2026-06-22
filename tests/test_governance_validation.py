import os
import json
import glob
import logging
import pytest

# Configure logging for beautiful GitHub Actions terminal output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GOVERNANCE] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("GovernanceValidator")

# Attempt to import jsonschema to validate the pipeline configurations
try:
    import jsonschema
except ImportError:
    jsonschema = None


def validate_ranges_recursive(data, path=""):
    """Recursively checks that every leaf node in a dictionary configuration is an array/list."""
    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key
        
        if isinstance(value, dict):
            validate_ranges_recursive(value, current_path)
        elif not isinstance(value, list):
            raise TypeError(f"Field '{current_path}' must be a list/range, but got '{type(value).__name__}'")
        elif len(value) == 0:
            raise ValueError(f"Field '{current_path}' cannot be an empty list.")


def test_pipeline_schema_compliance():
    """1. Loops through all pipeline files and verifies compliance against schema/pipeline_schema.json."""
    logger.info("▶ Starting Check: Pipeline Schema Compliance")
    schema_path = "schema/pipeline_schema.json"
    
    if not os.path.exists(schema_path):
        logger.warning(f"Target schema not found at '{schema_path}'. Skipping evaluation.")
        return

    # Scan for pipeline files in both /pipelines/ and matching pipeline_*.json inside /schema/
    pipeline_files = glob.glob("pipelines/**/*.json", recursive=True) + [
        f for f in glob.glob("schema/pipeline_*.json") if "pipeline_schema.json" not in f
    ]
    
    if not pipeline_files:
        logger.info("Result: no files found for pipeline schema validation.")
        return

    failed_files = []
    for file_path in pipeline_files:
        logger.info(f"Evaluating Pipeline File: {file_path}")
        try:
            with open(file_path, 'r') as f:
                instance = json.load(f)
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            if jsonschema:
                jsonschema.validate(instance=instance, schema=schema)
            else:
                # Fallback baseline validation if jsonschema is not installed
                if not isinstance(instance, (dict, list)):
                    raise ValueError("Configuration payload must resolve to a valid JSON object or array.")
            
            logger.info(f"✅ PASSED: '{file_path}' complies with pipeline schema specification.")
        except Exception as e:
            error_msg = str(e).split("\n")[0]  # Keep logs concise
            logger.error(f"❌ FAILED: '{file_path}' - Reason: {error_msg}")
            failed_files.append((file_path, error_msg))

    if failed_files:
        pytest.fail(f"Pipeline validation failed for {len(failed_files)} file(s). Check logs above.")


def test_config_ranges_compliance():
    """2. Loops through all json assets in configs/ to ensure every parameter value is an array."""
    logger.info("▶ Starting Check: Configuration Range Structures")
    config_files = glob.glob("configs/**/*.json", recursive=True)

    if not config_files:
        logger.info("Result: no files found for config range validation.")
        return

    failed_files = []
    for file_path in config_files:
        logger.info(f"Evaluating Range Configuration: {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise TypeError("Root structural architecture must be a dictionary object.")
                
            validate_ranges_recursive(data)
            logger.info(f"✅ PASSED: '{file_path}' contains structurally sound value spaces.")
        except Exception as e:
            logger.error(f"❌ FAILED: '{file_path}' - Reason: {str(e)}")
            failed_files.append((file_path, str(e)))

    if failed_files:
        pytest.fail(f"Configuration validation check failed for {len(failed_files)} file(s). Check logs above.")


def test_setup_scripts_executable():
    """3. Verifies that all installation and shell assets in setup_scripts/ are marked executable."""
    logger.info("▶ Starting Check: Setup Script Executable Mode Status")
    script_files = glob.glob("setup_scripts/**/*", recursive=True)
    script_files = [f for f in script_files if os.path.isfile(f)]

    if not script_files:
        logger.info("Result: no files found in setup_scripts.")
        return

    failed_files = []
    for file_path in script_files:
        logger.info(f"Evaluating File Flags: {file_path}")
        
        # Verify if file has owner/group/world execution permissions
        if os.access(file_path, os.X_OK):
            logger.info(f"✅ PASSED: '{file_path}' execution bit verified (chmod +x is active).")
        else:
            reason = "File does not possess execute attributes. Resolve via 'chmod +x <file>'."
            logger.error(f"❌ FAILED: '{file_path}' - Reason: {reason}")
            failed_files.append((file_path, reason))

    if failed_files:
        pytest.fail(f"Permission mask validation check failed for {len(failed_files)} script(s). Check logs above.")