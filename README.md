# GOUTAMIND Document Intelligence

> **From healthcare documents to evidence-linked claim intelligence.**

**GOUTAMIND Document Intelligence** is an evidence-driven document intelligence project for understanding heterogeneous healthcare claim documents.

Healthcare claims rarely arrive as clean, structured data. A single claim may contain emergency records, inpatient notes, diagnostic reports, medication records, administrative documents, billing information, and claim outputs — often combined into heterogeneous PDF bundles from different hospitals.

The challenge is not simply extracting text from PDFs.

The challenge is to understand **what each document represents, where information came from, how facts relate to clinical events, and how every derived insight can remain traceable to its source evidence.**

---

## The Problem

A healthcare claim document bundle may contain:

- multiple logical documents inside a single PDF;
- different document layouts between hospitals;
- scanned and digitally generated pages;
- tables, forms, handwritten or image-based content;
- clinical and administrative information mixed together;
- repeated information with different levels of temporal precision;
- documents whose physical order does not represent clinical event order.

Therefore:

> **PDF extraction is not the same as document understanding.**

A reliable intelligence layer needs to preserve the relationship between the original document and every piece of information derived from it.

---

## The Approach

This project follows an **evidence-first architecture**.

```text
Healthcare Claim Document Bundle
                │
                ▼
      Document Understanding
                │
                ▼
        Document Structure
                │
                ▼
      Facts / Events / Evidence
                │
                ▼
       Clinical Interpretation
                │
                ▼
        Claim Intelligence
