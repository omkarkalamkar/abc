@SKA_mid @XTP-73592 @XTP-76068 @XTP-28347
Scenario Outline: Error Propagation Reported by TMC Mid AssignResources/ReleaseAllResources/Configure/End/EndScan/Scan Commands for Defective Subarray
		Given the telescope is ON state
		And the TMC subarray is in the <initialObsState> observation state
		When <command> is invoked on a defectiveSubsystem <defectiveSubsystem>
		Then the command failure is reported by subarray with error message
		Then the TMC SubarrayNode transitions to FAULT obsState
		Examples:
		            |initialObsState  | command          | defectiveSubsystem   |
		            |READY            | END              | CSP                  |
		            |SCANNING         | ENDSCAN          | CSP                  |
		            |READY            | SCAN             | CSP                  |
		            |READY            | END              | SDP                  |
		            |SCANNING         | ENDSCAN          | SDP                  |
		            |READY            | SCAN             | SDP                  |
		            |READY            | END              | DISH                 |
		            |SCANNING         | ENDSCAN          | DISH                 |
		            |READY            | SCAN             | DISH                 |
					|IDLE             | CONFIGURE        | CSP                  |
					|IDLE             | CONFIGURE        | SDP                  |
					|IDLE             | CONFIGURE        | DISH                 |
					|IDLE             | RELEASERESOURCES | CSP                  |
					|IDLE             | RELEASERESOURCES | SDP                  |
					|EMPTY            | ASSIGNRESOURCES  | CSP                  |
					|EMPTY            | ASSIGNRESOURCES  | SDP                  |



@SKA_mid @XTP-73592 @XTP-76069 @XTP-28347
	Scenario Outline: TimeOut Reported by TMC Mid AssignResources/ReleaseAllResources/Configure/End/EndScan/Scan Commands for Defective Subarray
		Given the telescope is ON state
		And the TMC subarray is in the <initialObsState> observation state
		When <command> is invoked on a <defectiveSubsystem> Subarray
		Then the command failure is reported by subarray with appropriate error message
		Then the TMC SubarrayNode transitions to FAULT obsState
		Examples:
		            |initialObsState  | command 		 | defectiveSubsystem   |
		            |READY            | END     		 | CSP                  |
		            |SCANNING         | ENDSCAN 		 | CSP                  |
		            |READY            | SCAN    		 | CSP                  |
		            |READY            | END     		 | SDP                  |
		            |SCANNING         | ENDSCAN 		 | SDP                  |
		            |READY            | SCAN    		 | SDP                  |
		            |SCANNING         | ENDSCAN 		 | DISH                 |
		            |READY            | SCAN    		 | DISH                 |
		            |READY            | END     		 | DISH                 |
					|IDLE             | CONFIGURE        | CSP                  |
					|IDLE             | CONFIGURE        | SDP                  |
					|IDLE             | CONFIGURE        | DISH                 |
					|IDLE             | RELEASERESOURCES | CSP                  |
					|IDLE             | RELEASERESOURCES | SDP                  |
					|EMPTY            | ASSIGNRESOURCES  | CSP                  |
					|EMPTY            | ASSIGNRESOURCES  | SDP                  |


@SKA_mid
Scenario Outline: TMC moves to FAULT obsState when CSP/SDP moves to FAULT obsState
		Given the telescope is ON state
		And the TMC subarray is in the <initialObsState> observation state
		When the <subsystem> subarray moves to FAULT obsState
		Then the TMC SubarrayNode transitions to FAULT obsState
		Examples:
		            |initialObsState  | subsystem   |
					|SCANNING         | SDP         |
					|SCANNING         | CSP         |
					|READY            | CSP         |
					|READY            | SDP         |
					# |IDLE             | SDP         |
		            # |IDLE             | CSP         |