.. _ops_apis:

=======================================
Operational Monitoring and Control APIs
=======================================

Control Commands
-----------------

TMC provides APIs in the form of Tango device commands for controlling the telescope as follows:

* :ref:`TelescopeOn <centralnode:telescope_on>`
* :ref:`TelescopeOff <centralnode:telescope_off>`
* :ref:`Standby <centralnode:telescope_standby>`
* `LoadDishCfg <https://developer.skao.int/projects/ska-tmc-centralnode/en/latest/knowledge_base/commands/mid/load_dish_cfg_command.html>`_

Monitoring of the telescope level activities can be done by reading/subscribing to 
the following Tango attributes exposed by Tango attributes exposed by 
.. :ref:`Central Node <components_cn>`:

* telescopeState
* telescopeHealthState
* telescopeAvailability
* transformedInternalModel

..  Additionally, monitoring of individual TMC component can be done by reading/subscribing 
    to the attributes exposed by various TMC components. Please refer to 
    #:ref:`Knowledge Base <knowledge_base>` > :ref:`Components <components>` 
    for more details.
