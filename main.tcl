#!/usr/bin/env tclsh
# ============================================================
# Venus-02 - Ground Control Command/Telemetry Verification
# Spacecraft Systems Integration & Test - Tcl Example
# ============================================================

# ----------------------------
# "Database" layer (stub)
# Replace these with real DB calls (SQLite, Postgres, REST, etc.)
# ----------------------------
proc db_get_commands_for_program {program} {
    # Example "new database commands" from Ground Control
    # Module -> {cmd_on cmd_off}
    return [dict create \
        Thermal    [dict create on CMD001A off CMD001B] \
        Propulsion [dict create on CMD002A off CMD002B] \
        Power      [dict create on CMD003A off CMD003B] \
    ]
}

proc db_get_telemetry_for_program {program} {
    # Example "new telemetry IDs"
    # Module -> telemetry id
    return [dict create \
        Thermal    TLM001 \
        Propulsion TLM002 \
        Power      TLM003 \
    ]
}

# ----------------------------
# Simulator interface (stub)
# Replace with your real simulator integration:
# e.g., socket, lab middleware, command server, etc.
# ----------------------------
namespace eval sim {
    variable state
    # default states
    array set state {
        TLM001 OFF
        TLM002 OFF
        TLM003 OFF
    }
}

proc sim_send_command {cmdId} {
    # In reality: send cmdId to simulator and check ACK/response.
    # Here we "apply" the command to the simulated telemetry state.
    switch -- $cmdId {
        CMD001A { set ::sim::state(TLM001) ON  }
        CMD001B { set ::sim::state(TLM001) OFF }
        CMD002A { set ::sim::state(TLM002) ON  }
        CMD002B { set ::sim::state(TLM002) OFF }
        CMD003A { set ::sim::state(TLM003) ON  }
        CMD003B { set ::sim::state(TLM003) OFF }
        default  { return -code error "SIM: Unknown Command ID: $cmdId" }
    }

    # Return a simple ACK structure (example)
    return [dict create ack true cmd $cmdId resultCode 200]
}

proc sim_read_telemetry {tlmId} {
    # In reality: request telemetry packet / subscribe + wait, then decode.
    if {![info exists ::sim::state($tlmId)]} {
        return -code error "SIM: Unknown Telemetry ID: $tlmId"
    }
    return [dict create id $tlmId value $::sim::state($tlmId)]
}

# ----------------------------
# Test utilities
# ----------------------------
proc assert_equal {actual expected message} {
    if {$actual ne $expected} {
        return -code error "ASSERT FAIL: $message | expected=$expected actual=$actual"
    }
}

proc wait_for_tlm_value {tlmId expected timeoutMs pollMs} {
    set start [clock milliseconds]
    while {([clock milliseconds] - $start) < $timeoutMs} {
        set pkt [sim_read_telemetry $tlmId]
        set val [dict get $pkt value]
        if {$val eq $expected} {
            return $pkt
        }
        after $pollMs
    }
    return -code error "TIMEOUT: $tlmId did not reach $expected within ${timeoutMs}ms"
}

# ----------------------------
# Core test: toggle a module ON then OFF and validate telemetry
# ----------------------------
proc test_module_toggle {module cmdOn cmdOff tlmId} {
    puts "=== TEST: $module (TLM=$tlmId, ON=$cmdOn, OFF_tf=$cmdOff) ==="

    # Send ON command
    set ackOn [sim_send_command $cmdOn]
    assert_equal [dict get $ackOn ack] true "$module ON command not acknowledged"

    # Verify telemetry becomes ON
    wait_for_tlm_value $tlmId ON 2000 100
    puts "PASS: $module telemetry is ON ($tlmId)"

    # Send OFF command
    set ackOff [sim_send_command $cmdOff]
    assert_equal [dict get $ackOff ack] true "$module OFF command not acknowledged"

    # Verify telemetry becomes OFF
    wait_for_tlm_value $tlmId OFF 2000 100
    puts "PASS: $module telemetry is OFF ($tlmId)"
    puts ""
}

# ----------------------------
# Main
# ----------------------------
proc main {} {
    set program "Korriban-02"

    # Pull "new database commands and telemetry"
    set cmdMap [db_get_commands_for_program $program]
    set tlmMap [db_get_telemetry_for_program $program]

    puts "Running Korriban-02 Command/Telemetry verification against simulators..."
    puts ""

    foreach module [dict keys $cmdMap] {
        set cmdOn  [dict get $cmdMap $module on]
        set cmdOff [dict get $cmdMap $module off]
        set tlmId  [dict get $tlmMap $module]

        test_module_toggle $module $cmdOn $cmdOff $tlmId
    }

    puts "ALL TESTS COMPLETED"
}

main