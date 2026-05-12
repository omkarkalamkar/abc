TMC (Telescope Monitoring and Control) Mid
==========================================

The Telescope Monitor and Control (TMC) is the software module identified to perform the telescope management, 
and data management functions of the Telescope Manager. 
Main responsibilities identified for TMC are:
 
  * Operational monitoring and control of the telescope
  * Support execution of astronomical observations
  * Manage telescope hardware and software subsystems in order to perform astronomical observations
  * Manage the engineering data to support operators, maintainers, engineers and science users to achieve their goals
  * Determine telescope state.

To support these responsibilities, the TMC performs high-level functions such as Observation Execution, 
Monitoring and Control of Telescope, Resource Management, Configuration Management, Alarm and Fault Management, 
and Telescope Data Management (Historical data and Real time data).
These high level functions are again divided into lower level functions to perform the specific functionalities.

The TMC has a hierarchy of control nodes for Mid-
Central Node, Subarray Node, SDP Leaf Nodes, CSP Leaf Nodes and Dish Leaf Nodes

The components(CentralNode, SubarrayNode, Leaf Nodes) of the TMC system are integrated in the `TMC integration repository
<https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-mid-integration>`_, which contains
the Helm chart to deploy the TMC. More details on the design of the TMC and how
to run it locally or in the integration environment can be found in the :ref:`Documentation 
<getting_started>`

Impact of AdminMode on command execution
-----------------------------------------

1. The command invocation is **not allowed** from **TMC CentralNode** if the adminMode of any subsystem's controller is  either **OFFLINE** or **NOT_FITTED**
2. The command invocation is **not allowed** from **TMC SubarrayNode** if the adminMode of any subsystem's subarray is  either **OFFLINE** or **NOT_FITTED**
3. The command invocation is **allowed** if the adminMode of subsystem is either **ONLINE** or **ENGINEERING**
