.. _deployment:

==================
Deployment
==================

Standard deployment
====================

The TMC Mid is packaged as a `helm chart <https://helm.sh/>`_ and can be
deployed using helm commands. The default deployment configuration is
assumed to be the SKA production environment. In the current version,
TMC supports `one` subarray operation with four dishes. Following list shows
default number of instances deployed for each of the TMC component.

#. Central Node - 1
#. Subarray Node - 1
#. CSP Master Leaf Node - 1
#. CSP Subarray Leaf Node - 1
#. SDP Master Leaf Node - 1
#. SDP Subarray Leaf Node - 1
#. Dish Leaf Node - 4
#. Resource Monitor - 1


.. warning:: The number of instances of Central Node, SDP Master Leaf Node and
    CSP Master Leaf Node should always be one even
    though it is technically possible to deploy multiple instances.

To deploy the TMC use following command on the terminal:

.. code-block:: python

    helm install my-tmc-release https://artefact.skao.int/repository/helm-internal/ska-tmc-mid --namespace ska-tmc-mid

It is possible to customize the deployment as per need. To do so, the
`values.yaml` file in TMC chart needs to be modified. The same can be done by
using `--set` option in the command line while using the `helm install`
command.

Basic Customization options
===========================

Number of subarrays
--------------------

The number of subarrays can be deployed according to the need. A variable
named **subarray_count** need to be set to the desired value. This option
affects the number of instances of following components.

#. Subarray Node
#. CSP Subarray Leaf Node
#. SDP Subarray Leaf Node

global.dishids (changed)
----------------------------

The **global.dishids**  parameter has been refactored to support dynamic scaling.
This is **not a new feature**, but a change to existing behavior.

Example:

.. code-block:: yaml

   global:
     dishids:
       count: 4
       identifiers:
         - SKA001
         - SKA002
         - SKA003
         - SKA004


Tango host
----------

This option allows to specify the desired Tango facility. The variable
**tango_host** is used to specify the tango facility. By default, the value
of this variable is set to `databaseds-tango-base-test:10000`.

Dish Name
---------

This options allows the user to control the dishes deployed with non-standard
naming conventions. The variable **dish_name** defined in the global section
should be set with comma separated string values of the Dish TRLs.

    Default Value for dish leaf node is

    #. **Dish Leaf Node** : ["001", "036", "063", "100"]

Command timeout
---------------

The ``CommandTimeout`` attribute is introduced to allow updating the timeout value
for commands without requiring a redeployment. This provides flexibility in tuning
the timeout dynamically at runtime based on operational needs.

The ``CommandTimeOutDefault`` property is also introduced, which can be used to set
a default timeout value during the deployment phase. This ensures that an initial
timeout value is preconfigured when the component starts for the first time.

Logging
-------

The basic setting for logging allows setting logging level of all TMC devices
via ``TMCLoggingLevel`` parameter in **global** section. By default, the
logging level is set to 4 (``INFO`` level). To set the logging level of one or
more specific component, refer to advanced cutomization options.

Usage
-----

* **CommandTimeout attribute**
  - Can be updated at runtime without redeployment.
  - Helps in adapting to varying command execution times.

* **CommandTimeOutDefault property**
  - Configurable in the deployment configuration (e.g., ``values.yaml``).
  - Sets the initial timeout value at startup.

This option sets the timeout value till which the TMC components wait for
completion of commands invoked on lower level Tango devices. This timeout
should be set for each TMC component. To set the desired timeout value,
navigate to **deviceServers -> <component name>** in `values.yaml` file.
Locate **CommandTimeOutDefault** variable and set an integer value equivalant in
seconds.

.. warning::
    When setting the command timeout values, it is essential to set bigger
    timeout values for Central Node and Subarray Node than any Leaf Node. This
    is because the as per TMC architecture, Central Node and Subarray Node are
    higher level in the hierarchy and Leaf Nodes are at lower level. The
    commands flow from Central Node, Subarray Node, to Leaf Nodes and then to the
    subsystems. The higher level nodes need to factor in the command timeout
    set on lower level components.

DishId-VCC Configuration
------------------------

This options allows the user to set the desired version of DishID-VCC map
configuration of the system at the time of TMC deployment. To set the desired
version, two values are required to be set. Navigate to
**deviceServers.centralnode** -> **DishVccConfig** section in the
**values.yaml** file. The variable **DishVccConfig** in this
section specifies the URI of the DishId-VCC configuration file. Currently, its
value defaults to
"car://gitlab.com/ska-telescope/ska-telmodel-data?ska-sdp-tmlite-repository-1.0.0#tmdata".

The variable **DishVccFilePath** specifies the respective file path of the configuration
file in the telmodel repo. Currently, its default values is set to
"instrument/ska1_mid_psi/ska-mid-cbf-system-parameters.json".

Global Pointing Model Configuration
-----------------------------------

TMC Mid supports Global Pointing Model (GPM) configuration starting from version 1.9.0.
The following parameters define the GPM setup:

**Key Parameters**:

**version**: Specified GPM version will be applied to all dishes during TMC initialization

**interface**: Defines the GPM schema interface URL

**data_sources_prefix**: Base URI for GPM data repositories (e.g., CAR URLs)

**file_path_prefix**: Relative path to GPM data within the repository.

.. warning::

   All parameters are mandatory — missing or incorrect values may cause the TMC to fail to apply
   the specified version of the GPM during initialization.

Except for version, all other parameters remain consistent across deployments and are used by the
**SetGlobalPointingModel** command to apply the specified version from the input JSON. Upon redeployment,
only these parameters can be modified.

These parameters are located under the **deviceServers.centralnode.global_pointing_model** section in the
**values.yaml** file.

For further information and details, please `click here <https://confluence.skatelescope.org/x/V4TtEQ>`_

**GlobalPointingModelStatus**: This central node attribute shows the current status of bandwise GPM applied to the dish.

kValue Configuration
------------------------

This option is used to set the valid range of dish k values. Navigate to
deviceServers.centralnode -> KValueValidRange section in the values.yaml file.
Set the **min** and **max** variables to specify lower and upper limit of the
valid range of dish k values.

Track table specific configuration
-----------------------------------

TBD: Add track table related config param here from dish pointing device.

Advanced Customization options
=====================================

Following are the advance options. These options are mainly useful for developers
and AIV engineers for testing purpose. Customizing these parameters should be
done carefully.


#. **file** : User can provide custom device server configuration file to nodes. Defaults are: `configuration files <https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration/-/blob/main/charts/ska-tmc-mid/data/>`_.

#. **enabled** : User can opt to disable any node by setting this value to False.Default is True for all nodes.

#. Variables under **global** section

    #. **domain** : This value is present under global. It is the domain name of TMC TANGO device. The value is set to "mid-tmc".
    #. **tmc_subarray_prefix** : This value is present under global, User can use this to change the FQDN prefix of SubarrayNode.
    #. **csp_subarray_ln_prefix** : This value is present under global, User can use this to change the FQDN prefix of CspSubarrayLeafNode.
    #. **sdp_subarray_ln_prefix** : This value is present under global, User can use this to change the FQDN prefix of SdpSubarrayLeafNode.
    #. **csp_master_ln** : This value is present under global, User can use this to change the FQDN of CspMasterLeafNode.
    #. **sdp_master_ln** : This value is present under global, User can use this to change the FQDN of SdpMasterLeafNode.
    #. **csp_subarray_prefix** : This value is present under global, User can use this to change the FQDN prefix of CSP Subarray.
    #. **sdp_subarray_prefix** : This value is present under global, User can use this to change the FQDN prefix of SDP Subarray.
    #. **csp_master** : This value is present under global, User can use this to change the FQDN of CSP Master.
    #. **sdp_master** : This value is present under global, User can use this to change the FQDN of SDP Master.
    #. **dish_suffix** : This value is present under global, User can use this to change the FQDN suffix of Dish Master.
    #. **dish_ln_prefix** : This value is present under global, User can use this to change the FQDN prefix of DishLeafNode.

#. **LoggingLevel** : To set the logging level of specific type of TMC component, \
   set this key under **deviceServers -> <component name>** in `values.yaml`. \
   This is optional parameter. If specified, it takes precedence over the value
   specified in ``TMCLoggingLevel`` in global section.


Component specific configuration
---------------------------------

This section specifies the configuration options for individual TMC component.
Navigate to **deviceServers.<component>** section in values.yaml file.

Central Node
^^^^^^^^^^^^^

    #. **DishIDs** : User can set this value to provide the ID's of dishes present in the deployment. Default is ["SKA001", "SKA036", "SKA063", "SKA100"]
    #. **LivelinessCheckPeriod** : This refers to the Period (in seconds) for the liveliness probe to monitor each device in a loop. Currently defaults to 2 seconds.
    #. **EventSubscriptionCheckPeriod** : This refers to the Period (in seconds) for the event subscriber to check the device subscriptions in a loop. Currently defaults to 2 seconds.
    #. **CommandTimeOutDefault** : This refers to the timeout (in seconds) for the command execution. Currently defaults to 120 seconds.
    #. **DishVccInitTimeout** : This refers to the timeout (in seconds) for the dish vcc initialization. Currently defaults to 180 seconds.
    #. **family** : This refers to the family name of CentralNode TANGO device. Currently defaults to "central-node".
    #. **member** : This refers to the member of CentralNode TANGO device. Currently defaults to "0".
    #. **SubarrayPrefix** :  This refers to the prefix for subarray devices. Currently defaults to "mid-tmc/subarray/".
    #. Few of the following properties are introduced inorder to configure the validation of Dish IDs in central node.
       The configuration was introduced so that later if the SKA Dish ID validation needs to be restored back to 197 or other, that can be done by manipulating following properties.
       These default properties are not supposed to be changed unless explicitly needed.

        #. **MeerKatDishIdLowerLimit** : This refers to allowed lower limit for Meerkat dish ids. Currently defaults to 0.
        #. **MeerKatDishIdUpperLimit** : This refers to allowed upper limit for Meerkat dish ids. Currently defaults to 63.
        #. **SkaDishIdLowerLimit** : This refers to allowed lower limit for SKA dish ids. Currently defaults to 1.
        #. **SkaDishIdUpperLimit** : This refers to allowed upper limit for SKA dish ids. Currently defaults to 999.

Subarray Node
^^^^^^^^^^^^^^

    #. **DishIDs** : User can set this value to provide the ID's of dishes present in the deployment. Default is ["SKA001", "SKA036", "SKA063", "SKA100"]
    #. **CspAssignResourcesInterfaceURL** : Interface version for CSP assign resources command. Currently defaults to "https://schema.skao.int/ska-csp-assignresources/2.0".
    #. **CspScanInterfaceURL** : Interface version for CSP scan command. Currently defaults to "https://schema.skao.int/ska-csp-scan/2.2".
    #. **SdpScanInterfaceURL** : Interface version for SDP scan command. Currently defaults to "https://schema.skao.int/ska-sdp-scan/1.1".
    #. **LivelinessCheckPeriod** : This refers to the Period (in seconds) for the liveliness probe to monitor each device in a loop. Currently defaults to 1.5 seconds.
    #. **EventSubscriptionCheckPeriod** : This refers to the Period (in seconds) for the event subscriber to check the device subscriptions in a loop. Currently defaults to 1.5 seconds.
    #. **CommandTimeOutDefault** : This refers to the timeout (in seconds) for the command execution. Currently defaults to 110 seconds.
    #. **AbortCommandTimeOut** : This refers to the timeout for the Subarray ABORTED obsState transition. Once the AbortCommandTimeOut exceeds, SubarrayNode transitions to obsState FAULT. Currently defaults to 130 seconds.
    #. **TelmodelSource** : This refers to the source of the telmodel model for the subarray. Currently defaults to "car://gitlab.com/ska-telescope/ska-telmodel-data?main#tmdata".
    #. **TelmodelPath** : This refers to the path of the telmodel model for the subarray. Currently defaults to "instrument/ska1_mid/layout/mid-layout.json".
    #. **ScanStartTimeOffset** : Offset for start_time for scan command in nanoseconds.
    #. **StartTimeEnabled** : Flag to enable/disable use of ScanStartTimeOffset.

SDP Subarray Leaf Node
^^^^^^^^^^^^^^^^^^^^^^^^

    #. **LivelinessCheckPeriod** : This refers to the Period (in seconds) for the liveliness probe to monitor each device in a loop. Currently defaults to 1.5 seconds.
    #. **EventSubscriptionCheckPeriod** : This refers to the Period (in seconds) for the event subscriber to check the device subscriptions in a loop. Currently defaults to 1.5 seconds.
    #. **CommandTimeOutDefault** : This refers to the timeout (in seconds) for the command execution. Currently defaults to 50 seconds.
    #. **AdapterTimeOut** : This refers to the timeout (in seconds) for the adapter creation. This property is for internal use. Currently defaults to 2 seconds.

SDP Master Leaf Node
^^^^^^^^^^^^^^^^^^^^^^^^

    #. **LivelinessCheckPeriod** : This refers to the Period (in seconds) for the liveliness probe to monitor each device in a loop. Currently defaults to 1.5 seconds.
    #. **EventSubscriptionCheckPeriod** : This refers to the Period (in seconds) for the event subscriber to check the device subscriptions in a loop. Currently defaults to 1.5 seconds.
    #. **AdapterTimeOut** : This refers to the timeout (in seconds) for the adapter creation. This property is for internal use. Currently defaults to 2 seconds.

CSP Master Leaf Node
^^^^^^^^^^^^^^^^^^^^^^^^

    #. **LivelinessCheckPeriod** : This refers to the Period (in seconds) for the liveliness probe to monitor each device in a loop. Currently defaults to 1.5 seconds.
    #. **EventSubscriptionCheckPeriod** : This refers to the Period (in seconds) for the event subscriber to check the device subscriptions in a loop. Currently defaults to 1.5 seconds.
    #. **AdapterTimeOut** : This refers to the timeout (in seconds) for the adapter creation. This property is for internal use. Currently defaults to 2 seconds.

CSP Subarray Leaf Node
^^^^^^^^^^^^^^^^^^^^^^^^

    #. **DelayCadence** : This refers to the time difference (in seconds) between each publication of delay values to the `delayModel` attribute on the `CspSubarrayLeafNode`. Currently defaults to 10 seconds.
    #. **DelayValidityPeriod** : This represents the duration (in seconds) for which delay values remain valid after being published. Currently defaults to 20 seconds.
    #. **DelayModelTimeInAdvance** : This indicates the time in seconds by which delay values need to be available in advance. Currently defaults to 30 seconds.
    #. **LivelinessCheckPeriod** :  his refers to the Period (in seconds) for the liveliness probe to monitor each device in a loop. Currently defaults to 1.5 seconds.
    #. **EventSubscriptionCheckPeriod** : This refers to the Period (in seconds) for the event subscriber to check the device subscriptions in a loop. Currently defaults to 1.5 seconds.
    #. **CommandTimeOutDefault** : This refers to the timeout (in seconds) for the command execution. Currently defaults to 50 seconds.
    #. **AdapterTimeOut** : This refers to the timeout (in seconds) for the adapter creation. This property is for internal use. Currently defaults to 2 seconds.
    #. **TelmodelSource** : This refers to the telmodel source for array layout. Currently defaults to "gitlab://gitlab.com/ska-telescope/ska-telmodel-data?main#tmdata".
    #. **TelmodelPath** : This refers to the telmodel path for array layout. Currently defaults to "instrument/ska1_mid/layout/mid-layout.json".

Dish Leaf Node
^^^^^^^^^^^^^^^^^^^^^^^^
    #. **LivelinessCheckPeriod** : This refers to the Period (in seconds) for the liveliness probe to monitor each device in a loop. Currently defaults to 1.5 seconds.
    #. **EventSubscriptionCheckPeriod** : This refers to the Period (in seconds) for the event subscriber to check the device subscriptions in a loop. Currently defaults to 1.5 seconds.
    #. **CommandTimeOutDefault** : This refers to the timeout (in seconds) for the command execution. Currently defaults to 90 seconds.
    #. **MaxTrackTableRetry** :This refers to the maximum retries for the programTrackTable write operation. Currently defaults to 3.
    #. **TrackTableRetryDuration** : This refers to the retry duration (in seconds) for programTrackTable write operation in seconds. Currently defaults to 0.2 seconds.
    #. **DishAvailabilityCheckTimeout** : This refers to the timeout for the dish availability check during intialisation. This property is for internal use. Currently defaults to 3 seconds.
    #. **AdapterTimeOut** : This refers to the timeout (in seconds) for the adapter creation. This property is for internal use. Currently defaults to 2 seconds.
    #. **WeatherStationDeviceNames** : TRL's of the weather stations.
    #. **MaxAllowedWindspeed** : Maximum permissible wind speed in m/s before triggering dish stow. Default value is 13.5 m/s.
    #. **MaxAllowedOpsWindspeed** : Maximum permissible ops wind speed in m/s before triggering dish stow. Default value is 10 m/s.
    #. **MaxAllowedGustWindspeed** : Maximum permissible gust wind speed in m/s before triggering dish stow. Default value is 20 m/s.
    #. **MaxAllowedWindspeedDifference** : Maximum permissible wind speed difference in m/s before triggering dish stow. Default value is 4.5 m/s.
    #. **WindspeedMeasurementTimeWindow** : Time window (in seconds) over which wind speed measurements are evaluated. Default is 1000.
    #. **GustWindspeedMeasurementTimeWindow** : Time window (in seconds) used to assess gust wind speed. Default is 3.
    #. **MeanWindspeedTimeWindow** : Time window (in seconds) for calculating the mean wind speed. Default is 600.
    #. **MaxAllowedOpsMeanWindspeedMeasurementTimeWindow** : Time window (in seconds) for evaluating the maximum allowed operational mean wind speed. Default is 600.
    #. **MaxTemperatureThreshold** : Maximum allowable temperature (°C) before protective action is triggered. Default is 40.
    #. **MinTemperatureThreshold** :  Minimum allowable temperature (°C) before protective action is triggered. Default is -5.
    #. **TimeDelta** : Maximum allowed time difference (in seconds) between successive measurements. Default is 1000.
    #. **TemperatureDelta** : Maximum permitted temperature variation (°C) within the defined time window. Default is 10.
    #. **EnableAutoStow**: Flag to enable or disable automatic stow. Default is true.

Dish Pointing Device
^^^^^^^^^^^^^^^^^^^^^^^^

    #. **TrackTableUpdateRate** : This refers to the rate (in seconds) at which a tracktable is supplied to the DishManager. Currently defaults to 50 seconds.
    #. **TrackTableInAdvance** : This refers to the time in advance at which programTrackTable needs to be provided. Currently defaults to 7 seconds.
    #. **ElevationMaxLimit** : This refers to the maximum elevation allowed for observation. Currently defaults to 90.0.
    #. **ElevationMinLimit** : This refers to the minimum elevation allowed for observation. Currently defaults to 15.0.
    #. **AzimuthMaxLimit** : This refers to the Maximum value of Azimuth where dish can point. Currently defaults to 270.0.
    #. **AzimuthMinLimit** : This refers to the Minimum value of Azimuth where dish can point. Currently defaults to -270.0.
    #. **SchedularQueuePreEntries** : ProgramTrackTable entries queued ahead in the track thread scheduler, primarily for developer-side debugging.
    #. **WeatherStationDeviceNames** : TRL's of the weather stations.
    #. **EventSubscriptionCheckPeriod** : Event subscription interval in seconds.
    #. **ProgramTrackTableSize**: This refers to the size of the programTrackTable. Defaults to 50 entries.

Resource Monitor
^^^^^^^^^^^^^^^^^^^^^

    #. **LivelinessCheckPeriod** : This defines how often (in seconds) the system checks if each connected device is active. The default value is 0.5 seconds.
    #. **EventSubscriptionCheckPeriod** :  This defines the period (in seconds) for the event subscriber to verify and maintain active subscriptions. Currently defaults to 0.5 seconds.
    #. **family** :  This refers to the family name of the Resource Monitor Tango device. Currently defaults to **"resource-monitor"**.
