from tee_plugin_gamesdk.tee_plugin import TeePlugin
options = {
    "id": "test_tee_worker",
    "name": "Test TEE Worker",
    "description": "An example TEE Plugin for testing.",
    "type": "GCS"
}
# Initialize the TeePlugin with your options
tee_plugin = TeePlugin(options)

# Generate Attestation report
get_attestation_report_fn = tee_plugin.get_function('get_attestation_report')
get_attestation_report_fn("Hello world!")