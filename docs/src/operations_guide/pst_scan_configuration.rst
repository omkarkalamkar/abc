.. _`PST Scan Configuration Through TMC`:

==========================================
PST Scan Configuration Through TMC
==========================================

Overview
--------
This page provides the steps to execute PST observations.

1. AssignResources
------------------

It is required to provide the pst beam ids (list) as part of AssignResources command input JSON.

Example:

.. code-block:: none

    {
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.4",
        "transaction_id": "txn-....-00001",
        "subarray_id": 1,
        "csp": {
            "pst": {
                "pst_beam_ids": [
                    1
                ]
            }
        },
    ...
    }

2. Configure
------------

TMC supports 4 PST processing modes. TMC support only one mode at a time. The JSON example are as follows:

A. **Voltage Recorder mode**

Example:

.. code-block:: none

    {
        "interface": "https://schema.skao.int/ska-tmc-configure/6.0",
        "transaction_id": "",
        "pointing": {
            "target": {
                "reference_frame": "ICRS",
                "target_name": "Polaris Australis",
                "ra": "21:08:47.92",
                "dec": "-88:57:22.9",
                "ca_offset_arcsec": 0.0,
                "ie_offset_arcsec": 0.0
            },
            "correction": "UPDATE"
        },
        "dish": {
            "receiver_band": "1"
        },
        "csp": {
            "interface": "https://schema.skao.int/ska-csp-configurescan/8.3",
            "common": {
                "config_id": "sbi-mvp01-20200325-00001-science_A",
                "frequency_band": "2",
                "eb_id": "eb-m001-20230712-56789"
            },
            "pst": {
                "beams": [{
                "beam_id": 1,
                "scan": {
                    "centre_frequency": 10550000000.0,
                    "total_bandwidth": 2496345600.0,
                    "observer_id": "jdoe",
                    "project_id": "project1",
                    "receiver_id": "receiver3",
                    "max_scan_length": 20000.0,
                    "subint_duration": 30.0,
                    "receptors": ["SKA001", "SKA036"],
                    "receptor_weights": [0.4, 0.6],
                    "pst_processing_mode": "VOLTAGE_RECORDER",
                    "target": {
                        "target_name": "J1921+2153",
                        "reference_frame": "icrs",
                        "attrs": {
                            "c1": 290.43672917,
                            "c2": 21.884,
                            "epoch": 2000.0
                        }
                    }
                }
            }]
            },
            "transaction_id": "txn-....-00001",
            "midcbf": {
                "pst_bf": {
                    "processing_regions": [{
                        "fsp_ids": [5],
                        "start_freq": 495075840,
                        "channel_count": 3700,
                        "timing_beams": [{
                            "timing_beam_id": 1,
                            "receptors": ["SKA001", "SKA036"]
                        }]
                    }]
                }
            }
        },
        "sdp": {
            "interface": "https://schema.skao.int/ska-sdp-configure/0.4",
            "scan_type": "target:a"
        },
        "tmc": {
            "scan_duration": 5.0,
            "partial_configuration": false
        }
    }


B. **Flow Through mode**

Example:

.. code-block:: none

    {
        "interface": "https://schema.skao.int/ska-tmc-configure/6.0",
        "transaction_id": "",
        "pointing": {
            "target": {
                "reference_frame": "ICRS",
                "target_name": "Polaris Australis",
                "ra": "21:08:47.92",
                "dec": "-88:57:22.9",
                "ca_offset_arcsec": 0.0,
                "ie_offset_arcsec": 0.0
            },
            "correction": "UPDATE"
        },
        "dish": {
            "receiver_band": "1"
        },
        "csp": {
            "interface": "https://schema.skao.int/ska-csp-configurescan/8.3",
            "common": {
                "config_id": "sbi-mvp01-20200325-00001-science_A",
                "frequency_band": "2",
                "eb_id": "eb-m001-20230712-56789"
            },
            "pst": {
                "beams": [{
                "beam_id": 1,
                "scan": {
                    "centre_frequency": 10550000000.0,
                    "total_bandwidth": 2496345600.0,
                    "observer_id": "jdoe",
                    "project_id": "project1",
                    "receiver_id": "receiver3",
                    "max_scan_length": 20000.0,
                    "subint_duration": 30.0,
                    "receptors": ["SKA001", "SKA036"],
                    "receptor_weights": [0.4, 0.6],
                    "pst_processing_mode": "FLOW_THROUGH",
                    "target": {
                        "target_name": "J1921+2153",
                        "reference_frame": "icrs",
                        "attrs": {
                            "c1": 290.43672917,
                            "c2": 21.884,
                            "epoch": 2000.0
                        }
                    },
                    "ft": {
                        "channel_polarisation_selection": {
                            "channels": [0, 100],
                            "polarisations": "Both"
                        },
                        "rescale": {
                            "algorithm": "MedianMAD",
                            "periodic_update": true,
                            "timescale": 1.0
                        },
                        "requantisation": {
                            "num_bits_out": 4,
                            "scale": 1.0
                        }
                    }
                }
            }]
            },
            "transaction_id": "txn-....-00001",
            "midcbf": {
                "pst_bf": {
                    "processing_regions": [{
                        "fsp_ids": [5],
                        "start_freq": 495075840,
                        "channel_count": 3700,
                        "timing_beams": [{
                            "timing_beam_id": 1,
                            "receptors": ["SKA001", "SKA036"]
                        }]
                    }]
                }
            }
        },
        "sdp": {
            "interface": "https://schema.skao.int/ska-sdp-configure/0.4",
            "scan_type": "target:a"
        },
        "tmc": {
            "scan_duration": 5.0,
            "partial_configuration": false
        }
    }

C. **Pulsar Timing mode**

Example:

.. code-block:: none

    {
        "interface": "https://schema.skao.int/ska-tmc-configure/6.0",
        "transaction_id": "",
        "pointing": {
            "target": {
                "reference_frame": "ICRS",
                "target_name": "Polaris Australis",
                "ra": "21:08:47.92",
                "dec": "-88:57:22.9",
                "ca_offset_arcsec": 0.0,
                "ie_offset_arcsec": 0.0
            },
            "correction": "UPDATE"
        },
        "dish": {
            "receiver_band": "1"
        },
        "csp": {
            "interface": "https://schema.skao.int/ska-csp-configurescan/8.3",
            "common": {
                "config_id": "sbi-mvp01-20200325-00001-science_A",
                "frequency_band": "2",
                "eb_id": "eb-m001-20230712-56789"
            },
            "pst": {
                "beams": [{
                "beam_id": 1,
                "scan": {
                    "centre_frequency": 10550000000.0,
                    "total_bandwidth": 2496345600.0,
                    "observer_id": "jdoe",
                    "project_id": "project1",
                    "receiver_id": "receiver3",
                    "max_scan_length": 20000.0,
                    "subint_duration": 30.0,
                    "receptors": ["SKA001", "SKA036"],
                    "receptor_weights": [0.4, 0.6],
                    "pst_processing_mode": "PULSAR_TIMING",
                    "target": {
                        "target_name": "J1921+2153",
                        "reference_frame": "icrs",
                        "attrs": {
                            "c1": 290.43672917,
                            "c2": 21.884,
                            "epoch": 2000.0
                        }
                    },
                    "pt": {
                        "dispersion_measure": 100.0,
                        "rotation_measure": 0.0,
                        "ephemeris": "",
                        "pulsar_phase_predictor": "",
                        "output_frequency_channels": 1,
                        "output_phase_bins": 64,
                        "num_sk_config": 1,
                        "sk_config": [{
                            "sk_range": [0.8, 0.9],
                            "sk_integration_limit": 100,
                            "sk_excision_limit": 25.0
                        }],
                        "target_snr": 0.0
                    }
                }
            }]
            },
            "transaction_id": "txn-....-00001",
            "midcbf": {
                "pst_bf": {
                    "processing_regions": [{
                        "fsp_ids": [5],
                        "start_freq": 495075840,
                        "channel_count": 3700,
                        "timing_beams": [{
                            "timing_beam_id": 1,
                            "receptors": ["SKA001", "SKA036"]
                        }]
                    }]
                }
            }
        },
        "sdp": {
            "interface": "https://schema.skao.int/ska-sdp-configure/0.4",
            "scan_type": "target:a"
        },
        "tmc": {
            "scan_duration": 5.0,
            "partial_configuration": false
        }
    }

C. **Detected Filterbank**

Example:

.. code-block:: none

    {
        "interface": "https://schema.skao.int/ska-tmc-configure/6.0",
        "transaction_id": "",
        "pointing": {
            "target": {
                "reference_frame": "ICRS",
                "target_name": "Polaris Australis",
                "ra": "21:08:47.92",
                "dec": "-88:57:22.9",
                "ca_offset_arcsec": 0.0,
                "ie_offset_arcsec": 0.0
            },
            "correction": "UPDATE"
        },
        "dish": {
            "receiver_band": "1"
        },
        "csp": {
            "interface": "https://schema.skao.int/ska-csp-configurescan/8.3",
            "common": {
                "config_id": "sbi-mvp01-20200325-00001-science_A",
                "frequency_band": "2",
                "eb_id": "eb-m001-20230712-56789"
            },
            "pst": {
                "beams": [{
                "beam_id": 1,
                "scan": {
                    "centre_frequency": 10550000000.0,
                    "total_bandwidth": 2496345600.0,
                    "observer_id": "jdoe",
                    "project_id": "project1",
                    "receiver_id": "receiver3",
                    "max_scan_length": 20000.0,
                    "subint_duration": 30.0,
                    "receptors": ["SKA001", "SKA036"],
                    "receptor_weights": [0.4, 0.6],
                    "pst_processing_mode": "DETECTED_FILTERBANK",
                    "target": {
                        "target_name": "J1921+2153",
                        "reference_frame": "icrs",
                        "attrs": {
                            "c1": 290.43672917,
                            "c2": 21.884,
                            "epoch": 2000.0
                        }
                    },
                    "df": {
                        "dispersion_measure": 100.0,
                        "output_frequency_channels": 1,
                        "stokes_parameters": "Q",
                        "num_bits_out": 16,
                        "time_decimation_factor": 10,
                        "frequency_decimation_factor": 4,
                        "requantisation_scale": 1.0,
                        "requantisation_length": 1.0
                    }
                }
            }]
            },
            "transaction_id": "txn-....-00001",
            "midcbf": {
                "pst_bf": {
                    "processing_regions": [{
                        "fsp_ids": [5],
                        "start_freq": 495075840,
                        "channel_count": 3700,
                        "timing_beams": [{
                            "timing_beam_id": 1,
                            "receptors": ["SKA001", "SKA036"]
                        }]
                    }]
                }
            }
        },
        "sdp": {
            "interface": "https://schema.skao.int/ska-sdp-configure/0.4",
            "scan_type": "target:a"
        },
        "tmc": {
            "scan_duration": 5.0,
            "partial_configuration": false
        }
    }


There is no change for other commands and their JSON examples.