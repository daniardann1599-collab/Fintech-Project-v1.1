from __future__ import annotations

from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from app.models.entities import Account, Transfer


ISO_NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"


def _tag(name: str) -> str:
    return f"{{{ISO_NAMESPACE}}}{name}"


def _add_child(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    node = ET.SubElement(parent, _tag(tag))
    if text is not None:
        node.text = text
    return node


def _bank_code_from_iban(iban: str) -> str:
    if not iban or len(iban) < 8:
        return "0000"
    return iban[4:8]


def build_pacs008(
    transfer: Transfer,
    from_account: Account,
    to_account: Account,
    debtor_name: str,
    creditor_name: str,
) -> tuple[str, str, str]:
    ET.register_namespace("", ISO_NAMESPACE)

    doc = ET.Element(_tag("Document"))
    root = ET.SubElement(doc, _tag("FIToFICstmrCdtTrf"))

    msg_id = f"PACS008-{transfer.id}"
    now = datetime.now(timezone.utc).isoformat()

    grp_hdr = ET.SubElement(root, _tag("GrpHdr"))
    _add_child(grp_hdr, "MsgId", msg_id)
    _add_child(grp_hdr, "CreDtTm", now)
    _add_child(grp_hdr, "NbOfTxs", "1")
    sttlm_inf = ET.SubElement(grp_hdr, _tag("SttlmInf"))
    _add_child(sttlm_inf, "SttlmMtd", "CLRG")

    tx = ET.SubElement(root, _tag("CdtTrfTxInf"))
    pmt_id = ET.SubElement(tx, _tag("PmtId"))
    _add_child(pmt_id, "InstrId", msg_id)
    _add_child(pmt_id, "EndToEndId", f"E2E-{transfer.id}")
    _add_child(pmt_id, "TxId", str(transfer.id))

    amt = ET.SubElement(tx, _tag("IntrBkSttlmAmt"), Ccy=from_account.currency)
    amt.text = f"{transfer.amount:.2f}"
    _add_child(tx, "IntrBkSttlmDt", datetime.now(timezone.utc).date().isoformat())

    debtor = ET.SubElement(tx, _tag("Dbtr"))
    _add_child(debtor, "Nm", debtor_name)
    debtor_acct = ET.SubElement(tx, _tag("DbtrAcct"))
    debtor_id = ET.SubElement(debtor_acct, _tag("Id"))
    _add_child(debtor_id, "IBAN", from_account.iban)

    creditor = ET.SubElement(tx, _tag("Cdtr"))
    _add_child(creditor, "Nm", creditor_name)
    creditor_acct = ET.SubElement(tx, _tag("CdtrAcct"))
    creditor_id = ET.SubElement(creditor_acct, _tag("Id"))
    _add_child(creditor_id, "IBAN", to_account.iban)

    rmt = ET.SubElement(tx, _tag("RmtInf"))
    _add_child(rmt, "Ustrd", f"Transfer {transfer.id}")

    xml_payload = ET.tostring(doc, encoding="utf-8", xml_declaration=True).decode("utf-8")
    from_bank = _bank_code_from_iban(from_account.iban)
    to_bank = _bank_code_from_iban(to_account.iban)
    return xml_payload, from_bank, to_bank
