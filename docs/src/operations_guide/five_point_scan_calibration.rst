.. _`Five Point Calibration Scan`:

TMC Five-Point Calibration Scan
===================================

This guide provides instructions for performing a **five-point calibration scan** with TMC.

The procedure is intended for operators, to establish pointing calibration solutions that will later be applied during science observations.

Overview
--------

A five-point calibration scan requires the resources must be assigned to the subarray and
subarray must be online and available to accept commands.

The calibration scan sequence includes:

* One pointing scan (reference) using the full configuration.
* Four offset scans using partial configuration. 

Together, these five scans provide data to derive calibration solutions and calibration solutions are available for science observations.

Step-by-Step Procedure
----------------------

1. **Confirm Subarray state**

   - Verify that the TMC Subarray Node is online, reachable, and available.
   - If not, assign resources and configure until available.

2. **Perform five calibration scans**

   The calibration requires **five consecutive configuration + scan cycles**:

   * One scan using a full configuration.
   * Four offset scans, each using a partial configuration that only changes the pointing offsets.
     All other subarray configuration parameters remain unchanged.

   For each cycle:

   - Send the appropriate ``Configure`` command (full or partial).
   - Send a ``Scan`` command.
   - Observe the state transitions: ``READY → SCANNING → READY``.

   .. note::

      The procedure is the same regardless of whether the configuration is
      full or partial (offset scans). The difference lies only in
      the pointing offsets provided.

   **Example offsets for partial configurations**

   +--------------------------------------+---------------------------------------------+
   | JSON file (example)                  | Offset details                              |
   +======================================+=============================================+
   | ``partial_configuration_1.json``     | CA offset = 0.0, IE offset = +5.0 arcsec    |
   +--------------------------------------+---------------------------------------------+
   | ``partial_configuration_2.json``     | CA offset = 0.0, IE offset = −5.0 arcsec    |
   +--------------------------------------+---------------------------------------------+
   | ``partial_configuration_3.json``     | CA offset = +5.0 arcsec, IE offset = 0.0    |
   +--------------------------------------+---------------------------------------------+
   | ``partial_configuration_4.json``     | CA offset = −5.0 arcsec, IE offset = 0.0    |
   +--------------------------------------+---------------------------------------------+

3. **Validate pointing**

   After each scan, verify that the dishes have updated their ``actualPointing`` values
   and that no errors were reported in the command results.

   The Dish Leaf Node exposes this attribute, which can be monitored to verify
   that the commanded pointing offsets are correctly applied.

4. **(Optional) Apply calibration for science scans**

   Once all five calibration scans are complete:

   - Send a `Configure_mid.json <https://developer.skao.int/projects/ska-schemas/en/latest/schemas/tmc/ska-tmc-configure.html>`_  command with the science configuration.
   - TMC automatically fetch the calibration solutions from SDP using the addresses defined in `receive_address_mid.json <https://developer.skao.int/projects/ska-schemas/en/latest/schemas/sdp/ska-sdp-recvaddrs.html>`_.
   - Confirm that calibration solutions are applied to the dishes.
   

   .. note::

      Applying calibration via ``Configure`` is a standard step before starting
      science observations. It is mentioned here only to highlight that the
      solutions obtained from the five-point scan will be applied at this stage.

Troubleshooting Calibration Issues
----------------------------------

If one of the calibration steps fails:

* **Check observation state transitions**

  - Confirm the Subarray moves to ``SCANNING`` during each scan and returns to ``READY``.

* **Inspect Dish Leaf Nodes**

  - Check the ``actualPointing`` attribute to confirm that commanded offsets are applied.

* **Verify JSON payloads**

  - Ensure offsets are correct and ``"partial_configuration": true`` is included.

* **Check calibration availability**

  - Confirm that SDP publishes calibration data at the expected addresses.

JSON Interface References
-------------------------

* `TMC Configure schema <https://developer.skao.int/projects/ska-schemas/en/latest/schemas/tmc/ska-tmc-configure.html>`_

* Example partial configurations (for reference/testing):

  **partial_configuration_1.json**

  .. code-block:: json

     {
         "interface": "https://schema.skao.int/ska-tmc-configure/2.2",
         "transaction_id": "txn-....-00002",
         "pointing": {
             "target": {
                 "ca_offset_arcsec": 0.0,
                 "ie_offset_arcsec": 5.0
             }
         },
         "tmc": {
             "partial_configuration": true
         }
     }

  **partial_configuration_2.json**

  .. code-block:: json

     {
         "interface": "https://schema.skao.int/ska-tmc-configure/2.2",
         "transaction_id": "txn-....-00003",
         "pointing": {
             "target": {
                 "ca_offset_arcsec": 0.0,
                 "ie_offset_arcsec": -5.0
             }
         },
         "tmc": {
             "partial_configuration": true
         }
     }

  **partial_configuration_3.json**

  .. code-block:: json

     {
         "interface": "https://schema.skao.int/ska-tmc-configure/2.2",
         "transaction_id": "txn-....-00004",
         "pointing": {
             "target": {
                 "ca_offset_arcsec": 5.0,
                 "ie_offset_arcsec": 0.0
             }
         },
         "tmc": {
             "partial_configuration": true
         }
     }

  **partial_configuration_4.json**

  .. code-block:: json

     {
         "interface": "https://schema.skao.int/ska-tmc-configure/2.2",
         "transaction_id": "txn-....-00005",
         "pointing": {
             "target": {
                 "ca_offset_arcsec": -5.0,
                 "ie_offset_arcsec": 0.0
             }
         },
         "tmc": {
             "partial_configuration": true
         }
     }

* `receive_address_mid.json <https://developer.skao.int/projects/ska-schemas/en/latest/schemas/sdp/ska-sdp-recvaddrs.html>`_ (used mainly for testing)
