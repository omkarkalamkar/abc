###########
Change Log
###########

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`_.

[1.21.0-rc.1]
*************
Updated
-------

* Support for Position Velocity Time pattern added.
* programTrackTable size is now configurable via `ProgramTrackTableSize` property in dish pointing device.

[1.20.0-rc.1]
*************
Added
-----

* Full support for pointing.field key in the Configure command.
* TMC DishLeafNode to support reference frame (TLE, AltAz) with old and ADR-63 json
* Enabled plane_to_sphere conversion and fixed x/y offset support for mapping scans.
* Integrated refactored BaseScanMapping (added build_data_for_observation, get_projection, get_trajectory_name, and get_radec_from_plane_to_sphere).

[1.19.0-rc.2]
*************
Fixed
-----

* Fix indentation issue in Changelog.md file causing error in docs job.


[1.19.0-rc.1]
*************
Fixed
-----

* HM-859:
    * Fixed an issue where SubarrayNode could remain stuck in CONFIGURING when
      a Configure command failed and command_in_progress was cleared before
      aggregation was triggered.

    * Fixed incorrect ObsState aggregation in scenarios where a subsystem
      command returned FAILED but no subsequent event triggered aggregation,
      preventing transition out of CONFIGURING (e.g. to FAULT).

    * Added a FAULT rule so FAILED results correctly propagate to a FAULT
      ObsState when applicable.

Updated
--------

* SAH-1882: Utilised following leaf node tags with log improvements,
  * ska-tmc-centralnode  - 1.1.0
  * ska-tmc-sdpleafnode  - 0.29.0
  * ska-tmc-cspleafnode  - 0.43.0
  * ska-tmc-dishleafnode - 0.41.2
  * ska-tmc-subarraynode - 1.2.2


[1.18.0-rc.2]
*************
Fixed
------
* SKB-1230: TMC allows correlation information under CBF to be optional for PST scan configuration.

Updated
--------
* SubarrayNode: Updated to use ska-schemas v1.35.0 where correlation information under CBF is optional in Configure command input.
* Utilized SubarrayNode v1.1.1


[1.18.0-rc.1]
*************
Updated
--------
* Upgraded TMC components to base class v1.4.0 and pytango to v10.1.2.
* Integrate CSP Subarray Leaf Node (v0.41.0) with static delays improvements.


[1.17.0-rc.1]
*************
Added
-----
* Added HealthInfo aggregation support in the ska-tmc-mid-integration node. 
  The node now processes HealthInfo events from SA, Dish, CSP and SDP devices and updates the aggregated healthInfo attribute accordingly.

Updated
--------
* The basic setting for logging allows setting logging level of all TMC  devices via ``TMCLoggingLevel`` parameter in global section.
* Updated component versions to align with HealthInfo support:
  * SubarrayNode: 0.51.2
  * SDP Leaf Node: 0.27.0
  * CSP Leaf Node: 0.40.0
  * Dish Leaf Node: 0.30.0

[1.16.0-rc.2]
*************
Fixed
-----
* Fixed documentation

[1.16.0-rc.1]
*************
Added
-----
* TMC is now able to stow the dish manually using SetStowMode command.
* Automatically using weather station data.
* Follwing are the properties introduced in dishleafnode
          weather_station_device_names: 
          max_allowed_wind_speed
          max_allowed_ops_wind_speed
          max_allowed_gust_wind_speed
          max_allowed_wind_speed_difference
          wind_speed_measurement_time_window
          gust_wind_speed_measurement_time_window
          mean_wind_speed_measurement_time_window
          max_allowed_ops_mean_wind_speed_measurement_time_window
          max_temp_threshold
          min_temp_threshold
          time_delta
          temp_delta 
          enable_auto_stow


[1.15.0-rc.1]
*************
Added
-----
* TMC supports PST Scan Configuration.
* Introduced property `StartTimeEnabled` to enable/disable parameter from Scan JSON.
* Added `ScanStartTimeOffset` property in chart configuration.

[1.13.0]
*************
Updated
-------
* TMC Mid chart final release aligning with dish lmc version 9.0.0

[1.13.0-rc.3]
*************
Updated
-------
* TMC Mid to align with the changes introduced in Dish 9.0.0 namely; Fixed Abort timeout error. 

[1.13.0-rc.2]
*************
Updated
-------
* TMC Mid to align with the changes introduced in Dish 9.0.0 namely; Fixed Abort timeout error. However the tag has wrong code base. It is not usable.

[1.14.0-rc.1]
*************
Added
-------
* TMC Mid Detects and reports mismatch in Dish Parameters.
* Utilised CentralNode tag to 0.28.1, SubarrayNode tag to 0.49.1, DishLeafNode - 0.29.1 and Simulator - 1.7.5
* Marked ska-tmc-mid restart device job test as xfail due to instability caused by device restart

Updated
-------
* TMC Scan command supports optional field start_time to comply with ADR-111.

Fixed
-----
* Improved Abort Retry mechanism to resolve SKB-1158

[1.13.0-rc.1]
*************
Updated
-------
* TMC Mid to align with the changes introduced in Dish 9.0.0 namely; Deprecated SetOperateMode() command which is orchestrated in the TMC Configure workflow.

[1.12.0]
********

Updated
-------
* Updated dish-leafnodes tag to 0.27.1 to support Configure attenuation, saturation threshold, and noise diode.
* Update SubarrayNodeFQDNs property data type from string to array
* Utilised latest version of Resource Monitor 0.5.0
* Utilised latest version of dishleafnode 0.27.2

Fixed
-----
* Remove keys from input(argin) not required by real CSP, causing command failures.

[1.12.0-rc.3]
*************
Fixed
-----
Remove keys from input(argin) not required by real CSP, causing command failures.

[1.9.0]
************
Updated
-------
* TMC Mid full release 1.9.0

[1.12.0-rc.2]
*************
Updated
-------
* Update SubarrayNodeFQDNs property data type from string to array
* Utilised latest version of Resource Monitor 0.5.0
* Utilised latest version of dishleafnode 0.27.2

[1.12.0-rc.1]
*************
Updated
-------
* Updated dish-leafnodes tag to 0.27.1 to support Configure attenuation, saturation threshold, and noise diode

[1.11.0-rc.1]
*************
Added
-----
* Introduced ResourceMonitor device in the ska-tmc-mid.
* Added device configuration and FQDN under chart templates.
* TMC Mid now supports reporting subarray allocations through the dishes attribute of the Resource Monitor.
* Updated documentation to include ResourceMonitor configuration details and usage.
* Utilised the latest ResourceMonitor release version v0.4.0 for integration and verification.

[1.10.0-rc.1]
*************
Added
-----
* Arraylayout work is integrated in TMC mid integration work
* Added two device property for CentralNode DefaultArrayLayoutSourceURIs, DefaultArrayLayoutPath
* TMC Mid now supports configuring attenuation, saturation threshold and noise diode via Mid TMC Configure command.

[1.9.0-rc.2]
************
Fixed
-----
* Verified the Band 5 observation in mid-psi environment with real subsystems dish, CSP, CBF

Added
-----
* Added new RTD page to document Array Layout support.

[1.9.0-rc.1]
************
Added
-----
* TMC Mid now supports Global Pointing Model (GPM) functionality.
* Introduced the SetGlobalPointingModel command to apply GPM to specified bands for specified dishes in the input.
* Added configurable properties — version, interface, data_sources_prefix, and file_path_prefix — for GPM setup.
* Introduced the GlobalPointingModelStatus attribute to monitor the GPM status.
* Added the gpmVersion attribute to the DishLeafNode to indicate the GPM version applied to each dish's bands.

[1.8.0-rc.3]
************
Fixed
-----
* Fixed issues observed in Band 5 down conversion testing

[1.8.0-rc.2]
************
Fixed
-----
* Renamed the dishes field in values.yaml to dishids for fixing the issue with dish helm chart

[1.8.0-rc.1]
************
Added
-----
* Added new documentation: `TMC Five-Point Calibration Scan` guide
  (five-point calibration scan procedure, JSON examples, and step-by-step instructions).
* Band 5 Downconverter (Band5DC) support in the TMC-MID integration chart.
* Added documentation related to Band 5 Downconverter (Band5DC) integration and usage.

Updated
--------
* ska-telmodel → v1.25.0
* ska-tmc-cdm → v14.0.0
* ska-tmc-subarraynode → v0.43.1
* ska-tmc-dishleafnode → v0.24.2

[1.7.1.rc.1]
************
Added
-----
* Added a new test case to verify Bug SKB-918, SKB-1013
* Updated the ska-tango-utils and ska-tango-base image to 0.4.24
* Updated TMC tags:
        sdpleafnodes:0.24.2
        tmccommon: 0.30.3

Removed
-------
* Removed invalid receive addresses jsons from data, because they were no longer required

[1.7.0-rc.2]
************
Added
-----
* Updated Subarray Node to update ObsState aggregation rule for Abort and Configure command.
* Updated TMC tags:
    subarraynode: 0.41.3

[1.7.0-rc.1]
************
Added
-----
* Added a new test case to verify Bug SKB-617:
  Ensure that the "Assign Resource" succeeds even when the SDP block is empty.
* Updated helper in common and also update image to 0.28.8
* Introduced `subarray_count` variable in `mock.yaml` to support configurable subarray scaling.
* CommandTimeout attribute is introduced which can help to update timeout without redeployment.
* CommandTimeOutDefault property is introduced which
  can be used to set default value at the time of deployment.
* Updated TMC tags:
    centralnode: 0.21.3
    subarraynode: 0.41.0
    sdpleafnodes:0.24.0
    cspsubarrayleafnode: 0.31.0
    dishleafnode:tag: 0.24.0
    tmccommon: 0.30.0

Changed
-------
* Refactored helm chart for scaling from now the global dishes variable accepts
  dish_id in ["SKA001","SKA002","SKA003", ....."SKA067","SKA100"]

Fixed
-----
* Fix for bug SKB-813.

[1.6.0]
*******
This is the final version of TMC Mid delivering features SP-5340 and SP-5341
Both the features improve TMC robustness by handling inconsistent subsystem obsStates.

Added
-----
* TMC Subarray moves to FAULT after command timed out
* TMC Restart command is updated to invoke abort and restart on sub system to bring obs state to EMPTY
* TMC Subarray is updated to transition Obs State to FAULT after command failure
* Fix for bug SKB-930

[1.6.0-rc.1]
************
Added
-----
* TMC Subarray moves to FAULT after command timed out
* TMC Restart command is updated to invoke abort and restart on sub system to bring obs state to EMPTY
* TMC Subarray is updated to transition Obs State to FAULT after command failure

[1.5.0-rc.2]
************
Added
-----
* Incorporated Cable/static delays in the TMC Mid.


[1.5.0-rc.1]
************
Added
-----
* Update command not allowed logic to allow command execution in adminmode ENGINEERING and ONLINE
* Updated SubarrayNode image to 0.35.0
* Updated sdpleafnode image to 0.23.2

Fixed
-----
* Healthstate based rejection of commands is removed.

[1.4.0-rc.1]
************
### Added
* Attribute on sdpleafnode named `assignResourcesSchemaVersion` which sets default version of
SDP assign resources schema if not set.

### Updated
* TMC Mid supports new TMC AssignResources json v2.2 with SDP v1.0.

### Fixed
* Hardcoding of sdpleafnode is now removed and attribute is created to make it
runtime configurable.This resolves SKB-927.


[1.3.0-rc.1]
************
### Added
  * TMC-Mid considers weather parameters while calculating the delay model
  * Validate SKB-932
  * Utilised centralnode v0.19.7 to validate SKB-860.
  * Utilised dishleafnode v0.23.1 with updated Abort command completion check.

[1.2.0-rc.5]
************
### Updated
  * Utilised latest version of centralnode v0.19.7 to resolve SKB-860
  * Utilised latest version of dishleafnode v0.23.1 to
    updated Abort command completion check.

[1.2.0-rc.4]
************
### Fixed
  * Updated version of weather station to resolve Bug SKB-932 : Operator
    not setting to true while utilising Weather Station device.

[1.2.0-rc.3]
************
### Added
  * Weather Station Device integrated which provides weather data for delay
    correction calculations.
  * Updated SDP leafnode tag to 0.22.3

[1.2.0-rc.2]
************
### Added
  * Implemented timeout and exception propagation for Abort and Restart commands

[1.2.0-rc.1]
************
### Added
  * TMC uses wrap sector to generate program track table
  * TMC performs track table generation based on Fixed Trajectory data
  * Partial Configure now supports updating individual configuration keys. The Dish Leaf Node applies changes only to the specified fields.

[1.1.0]
*******
### Added
  * Event Handlers are updated to remove event processing logic and handle it under component manager.
  * Updated Central node command execution logic for Dishes to send ON/OFF/STANDBY
      commands even if it fails for one dish , command will still be sent to other dishes.
  * Utilized refactored event manager in ska-tmc-centralnode version 0.19.5
  * ska-tmc-common version 0.27.5 is utilized for the same
### Fixed
  * As a part of SKB-517 resolution pointingState SLEW was accepted as valid Dish
      pointingState , so that TMC subarry can move to READY obsState.
      But it was found that sometimes TRACK event for the dish which used to
      come to TMC after it moves to READY was causing issues in obsState aggregation.
      Hence, going forward TRACK event will not be sent from Dish Leaf Node if
      command is not in progress.


[1.1.0-rc.1]
************
### Added
  * Event Handlers are updated to remove event processing logic and handle it under component manager.
  * Updated Central node command execution logic for Dishes to send ON/OFF/STANDBY
      commands even if it fails for one dish , command will still be sent to other dishes.
  * Utilized refactored event manager in ska-tmc-centralnode version 0.19.5
  * ska-tmc-common version 0.27.5 is utilized for the same
### Fixed
  * As a part of SKB-517 resolution pointingState SLEW was accepted as valid Dish
      pointingState , so that TMC subarry can move to READY obsState.
      But it was found that sometimes TRACK event for the dish which used to
      come to TMC after it moves to READY was causing issues in obsState aggregation.
      Hence, going forward TRACK event will not be sent from Dish Leaf Node if
      command is not in progress.

[1.0.0]
*******
### Fixed
  * Resolved SKB-879.
  * Fixed issue with configure by updating dishleafnode v0.22.2.
  * Ensured required parameters are provided before starting delay model calculation
  * Resolved SKB-837 by enabling the read of receiveAddresses before configure command
      and utilising it if the change event of receiveAddresses is empty.This is resolved by
      subarray node 0.32.2.
  * Fix issue with trajectory key by utilising dish leaf node tag 0.21.0.
  * Resolved the SKB-716.
  * Resolved SKB-714, SKB-690
### Updated
  * Improved health state aggregation logic using rule engine.
  * Utilised Abort API instead of AbortCommands.
  * Updated the TRLs of TMC mid devices as per ADR-9
    * ska_mid/tm_central/central_node - mid-tmc/central-node/0
    * ska_mid/tm_subarray_node/1 - mid-tmc/subarray/01
    * ska_mid/tm_leaf_node/csp_master - mid-tmc/leaf-node-csp/0
    * ska_mid/tm_leaf_node/sdp_master - mid-tmc/leaf-node-sdp/0
    * ska_mid/tm_leaf_node/csp_subarray01 - mid-tmc/subarray-leaf-node-csp/01
    * ska_mid/tm_leaf_node/sdp_subarray01 - mid-tmc/subarray-leaf-node-sdp/01
    * ska_mid/tm_leaf_node/d0001 - mid-tmc/leaf-node-dish/ska001
### Added
  * DishVccCommandStatus attribute added for central node
  * LoadDishCfg command is rejected if DishVccCommandStatus is in STAGING or IN PROGRESS
  * After TMC initialization is complete, the DishVccCommandStatus is updated to either COMPLETED or FAILED.
  * Added `domain` field in values.yaml. The domain is `mid-tmc`
  * Added `family` and `member` field in deviceServers of each controller leafnode device in values.yaml
  * Added `family` field in deviceServers of each subarray leafnode devices in value.yaml

[1.0.0-rc.5]
************
### Fixed
    * Resolved SKB-879.
    * Fix issue with configure by updating dishleafnode and cspleafnode.
    * Ensured required parameters are provided before starting delay model calculation

### Updated
    * Improved health state aggregation logic using rule engine.
    * Utilised Abort API instead of AbortCommands

[1.0.0-rc.4]
************
### Fixed
    * Resolved SKB-837 by enabling the read of receiveAddresses before configure command
      and utilising it if the change event of receiveAddresses is empty.This is resolved by
      subarray node 0.32.2.
    * Fix issue with trajectory key by utilising dish leaf node tag 0.21.0.

[1.0.0-rc.3]
************
* Resolved the SKB-716
* Updated the CentralNode image to 0.18.2
* DishVccCommandStatus attribute added for central node
* LoadDishCfg command is rejected if DishVccCommandStatus is in STAGING or IN PROGRESS
* After TMC initialization is complete, the DishVccCommandStatus is updated to either COMPLETED or FAILED.

[1.0.0-rc.2]
************
* Updated ska-tmc-sdpleafnodes v0.21.1 to fix hardcoded sdp configure interface 0.3.
* Updated ska-tmc-centralnode v0.18.1 (contains latest telmodel to fix SKB-672 for low side).

[1.0.0-rc.1]
************
* Resolved SKB-714, SKB-690
* Added `domain` field in values.yaml. The domain is `mid-tmc`
* Added `family` and `member` field in deviceServers of each controller leafnode device in values.yaml
* Added `family` field in deviceServers of each subarray leafnode devices in value.yaml
* Updated the TRLs of TMC low devices as per ADR-9
* ska_mid/tm_central/central_node - mid-tmc/central-node/0
* ska_mid/tm_subarray_node/1 - mid-tmc/subarray/01
* ska_mid/tm_leaf_node/csp_master - mid-tmc/leaf-node-csp/0
* ska_mid/tm_leaf_node/sdp_master - mid-tmc/leaf-node-sdp/0
* ska_mid/tm_leaf_node/csp_subarray01 - mid-tmc/subarray-leaf-node-csp/01
* ska_mid/tm_leaf_node/sdp_subarray01 - mid-tmc/subarray-leaf-node-sdp/01
* ska_mid/tm_leaf_node/d0001 - mid-tmc/leaf-node-dish/ska001
* Updated CentralNode version to 0.18.0
* Updated DishLeafNode version to 0.20.0
* Updated SdpLeafNode version to 0.21.0
* Updated CspLeafNode version to 0.24.0
* Updated SubarrayNode version to 0.30.1

[0.25.0-rc.4]
*************
* Updated event receiver from central node
* Tested  timeout and error propagation for Scan/EndScan/End
* Resolved SKB-709 caused due to dishleafnode unavailability

[0.25.0-rc.3]
*************
* Added Configure functionality for ADR-63 based json

[0.25.0-rc.2]
*************
* Fixed RTD

[0.25.0-rc.1]
*************
* Following bugs are fixed on the tmc-dish interface:
  * SKB-469
  * SKB-606
  * SKB-661
* Fixed SKB-658 on all the TMC devices.

[0.24.0]
********
* TMC Mid full release 0.24.0 as per REL-1555

[0.24.0-rc.3]
*************
* Utilised CDM v.12.6.0 on ska-tmc-subarraynode.

[0.24.0-rc.2]
*************
* Updated following TMC nodes:
  * SDP subarray leaf node to fix SKB-699.
  * Central Node to fix event receiver and telescope on command.
  * Subarry Node to fix abort aggregation and SKB-512.
  * Dish leaf node to fix abort lock and scheduler blocking issue.
  * Fixed bug SKB-516 and SKB-536.
  * CSP subarray leaf node to fix SKB-666
  * Fixed bug SKB-525.
  * Fixed bug SKB-665 on central node.

[0.24.0-rc.1]
*************
* Verified the TMC-CSP with ADR-99 interface updates

[0.23.0-rc.1]
*************
* Verified the TMC-Dish interface timeout and error propagation functionality

[0.22.8]
********
* Resolved SKB-467, SKB-495, SKB-511 and SKB-530
* Track command will not be invoked from Dish leaf node if pointingState of Dish is TRACK/SLEW

[0.22.6]
********
* Resolved SKB-509
* Updated TMC to support TMC-CSP Configure interface v.3.0

[0.22.8-rc.1]
*************
* Updated ska-tmc-centralnode v0.16.8 to resolve skb-495
* Updated ska-tmc-cspleafnode v0.21.2 to resolve skb-495 and skb-530

[0.22.7-rc.1]
*************
* Updated ska-tmc-dishleafnode v0.17.6 to resolve SKB-511 and SKB-467
* Track command will not be invoked from Dish leaf node if pointingState of Dish is TRACK/SLEW

[0.22.6-rc.1]
*************
* Updated ska-tmc-subarraynode v.0.23.4 to resolve SKB-509
* TMC supporting TMC-CSP Configure interface v.3.0

[0.22.5]
**********
* Updated dish leaf node version 0.17.3 to resolve SKB-502
* Updated central node to 0.16.4 to resolve SKB-434

[0.22.4]
************
Fixed *SKB-497*

[0.22.3]
************
*TMC Dish Pointing (ADR-95 and ADR-76)*
  * Utilise Dishleafnode v0.17.1 to use correction key from Config json.
  * Test cases are implemented for correction key [{UPDATE},{RESET},{MAINTAIN}].

[0.22.2]
************
*Read the Docs warnings addressed*


[0.22.1]
************
*Observation State Aggregation Logic improvements*
  * Rule engine is used to define rules for ObsState
  * EventDataStorage class introduced to store event related data

[0.22.0]
************
* Utilised base class v1.0.0 and pytango 9.5.0 on TMC nodes*
    * Utilised ska-tmc-common v0.17.6 for tango helper devices.
    * Implemented queue according to support base classes v1.0.0.
    * Refactored command allowed method to put commands in queue.
    * Implemented command allowed methods for observation-specific commands to allow/reject the queued task: `ResultCode.NOT_ALLOWED/ResultCode.REJECTED`.
    * Refactored error propagation implementation on SubarrayNode, CentralNode, and TMC leaf nodes to handle `longrunningcommandresult` attribute new format in case of raised exceptions.
    * Refactored error propagation implementation to handle `longrunningcommandresult` event for `ResultCode.NOT_ALLOWED`, `ResultCode.REJECTED`, and `ResultCode.FAILED`.
    * Refactored all the integration tests (pairwise and with mocks) for TMC Mid according to `longrunningcommandresult` attribute value.

* Utilised `cspsubarrayleafnode` v0.19.1 with fixed `SKB-413`: Mid Delay Model code pointing to wrong dishes.
    * Implemented antenna parameters objects to generate according to mid_json layout.
    * Corrected Mid Delay Model to point to SKA or MKT dish according to assigned receptors.

* Utilised `dishleafnode` v0.16.3 Patch release for `SKB-419` fix from branch `SAH-1566`.

[0.21.2]
************
* Fix image link reference for DishLeafNode.

[0.21.1]
************
* Resolve `SKB-419`.
* Resolve `SKB-384` -  Currently, across all devices in TMC, there are no polled attributes (after our work on `SKB-384`). TMC monitors the attributes of other devices using event subscription methods. Unlike polling, which involves continuous querying, event subscription relies on a push-based mechanism. When a device generates an event (such as an attribute value change), the Tango system notifies all subscribed clients. As a result, there is no ongoing polling loop; TMC only receives updates when events occur."
* Note: This release - `REL-1623` is from `SAH-1564`.

[0.21.0]
************
* Improvement as per ADR-76 changes are done in Dish Leaf node and Subarray Node.
* Enabled ProgramTrackTable.
* Fixed CORBA issues in dish leaf node while execution of commands.

[0.20.1]
************
* Integrate TMC-Dish Scan functionality implementation.
* This release is from branch `sah-1524`.

[0.20.0]
************
* `SP-4028` Delay Model Improvements.
* `SKB-329` and `SKB-330` bug fixes on `CspSubarrayLeafNode` v0.16.2.
* Updated affected BDD test case - `XTP-32140`.

[0.19.2]
***********
* Updated Subarray Node to v0.18.0 that resolves the `SKB-331` and gets rid of hardcoded interface values.
* Fix bug `SKB-337`.
* Updated the kValue range to 1 to 1177.
* kValue range is a device property.
* Configure command gets accepted if the kValue for assigned dishes is either all the same or all different.

[0.19.1]
************
* Intermediate chart with TMC updates to work with `dish-lmc` chart 3.0.0.
* Fixed issues in the tests.

[0.19.0]
************
* Aligned delay model json as per ADR-88.
* `DelayCadence`, `DelayValidity`, and `DelayAdvancedTime` values are configurable.
* Fixed `SKB-300`.

[0.18.0]
************
* Integrated `ska-tmc-dishleafnode` with program track table into `ska-tmc-mid-integration` (SP-3987).
