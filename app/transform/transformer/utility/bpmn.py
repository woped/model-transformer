"""Module for finding start and end events in BPMN processes.

This module provides utility functions to identify and return all start and end events
in a given BPMN process.
"""

from app.transform.transformer.models.bpmn.bpmn import Process


def find_start_events(process: Process):
    """Return all start events of a process."""
    return [se for se in process.start_events if se.get_in_degree() == 0]


def find_end_events(process: Process):
    """Return all end events of a process."""
    return [ee for ee in process.end_events if ee.get_out_degree() == 0]

