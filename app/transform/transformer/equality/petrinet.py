"""Methods to compare petri nets by comparing all nodes of all subprocesses."""

import logging

from app.transform.exceptions import PrivateInternalException
from app.transform.transformer.equality.utils import create_type_dict, to_comp_string
from app.transform.transformer.models.pnml.base import NetElement, ToolspecificGlobal
from app.transform.transformer.models.pnml.pnml import Arc, Net

logger = logging.getLogger(__name__)


def petri_net_element_to_comp_value(e: NetElement | Arc):
    """Returns a comparable concatenation of a petri net element."""
    if isinstance(e, ToolspecificGlobal):
        return to_comp_string(e.resources)
    elif isinstance(e, NetElement):
        return to_comp_string(e.id, e.name, e.toolspecific)
    elif isinstance(e, Arc):
        return to_comp_string(e.source, e.target, e.toolspecific)
    else:
        raise PrivateInternalException(f"Not supported Petri Net Element: {type(e)}")


def petri_net_type_map(pn: Net):
    """Returns a by type grouped dictionary of the petri net element."""
    return create_type_dict(
        [*pn.transitions, *pn.places, *pn.arcs], petri_net_element_to_comp_value
    )


def get_all_nets_by_id(pn: Net, m: dict[str, Net]):
    """Get all nested nets as a dictionary by ID (Recursive function)."""
    if pn.id is not None and pn.id not in m:
        m[pn.id] = pn
    if len(pn.pages) == 0:
        return
    for page in pn.pages:
        if pn.id is None and page.id is None:
            raise PrivateInternalException("page of subnet  must have id")
        m[page.id or page.net.id or ""] = page.net
        get_all_nets_by_id(page.net, m)


def compare_pnml(pn1: Net, pn2: Net):
    """Returns a boolean if the diagrams are equal and an optional error message."""
    logger.debug("Comparing two Petri net models")
    pn1_nets: dict[str, Net] = {}
    get_all_nets_by_id(pn1, pn1_nets)
    pn2_nets: dict[str, Net] = {}
    get_all_nets_by_id(pn2, pn2_nets)
    
    logger.debug(f"PN1 has {len(pn1_nets)} nets, PN2 has {len(pn2_nets)} nets")

    if pn1_nets.keys() != pn2_nets.keys():
        logger.warning("PNML comparison failed: Different subnet IDs")
        return False, "Different subnet IDs"

    errors = []
    for net_id, net1 in pn1_nets.items():
        net2 = pn2_nets[net_id]

        pn1_types = petri_net_type_map(net1)
        pn2_types = petri_net_type_map(net2)

        if len(pn1_types) != len(pn2_types):
            return False, "Different Elements"

        for k in pn1_types.keys():
            if pn1_types[k] != pn2_types[k]:
                diff_1_to_2 = pn1_types[k].difference(pn2_types[k])
                diff_2_to_1 = pn2_types[k].difference(pn1_types[k])
                errors.append(
                    f"{net_id}\n{k} difference equality| 1 to 2: {diff_1_to_2} | 2 to 1: {diff_2_to_1}"
                )
    if len(errors) > 0:
        joined_errors = "\n".join(errors)
        logger.warning(f"PNML comparison failed with {len(errors)} differences")
        return False, f"Issues petrinet equality for types:\n{joined_errors}"
    logger.debug("PNML comparison successful: Models are equal")
    return True, None

