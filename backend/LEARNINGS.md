
# Technical Learnings – FactorTrace



This is a living log of deep technical rabbit holes (Pint, EXIOBASE, XBRL, etc.).  

Each entry should be something you'd want Future You (or an agent) to reuse.



---



## 1. Pint & Fuel Density Contexts  

**Date:** 2024-11-30  

**Topic:** Converting volume (L) to mass (kg) for fuels



**What I learned**



- Pint cannot convert `L` → `kg` without a density context.

- For fuels like diesel, you must define a custom context (e.g. 0.835 kg/L).

- Contexts are opt-in and used with a `with ureg.context("name")` block.



**Code Pattern**



```python

import pint



ureg = pint.UnitRegistry()



diesel_context = pint.Context("diesel")

diesel_context.add_transformation("liter", "kilogram", lambda ureg, x: x * 0.835)

ureg.add_context(diesel_context)



with ureg.context("diesel"):

    mass = 100 * ureg.liter

    mass_kg = mass.to("kg")

Gotchas





Be explicit: different fuels have different densities.

Contexts must be documented (for audit) – include source of density values.

Do not silently assume densities without at least a comment and reference.







2. EXIOBASE / MRIO Basics



Date: 2024-11-30

Topic: Using EXIOBASE for spend-based factors



What I learned





EXIOBASE is a multi-regional input–output (MRIO) database, typically accessed via pymrio.

The raw files are huge (GB-level); you should not load them ad hoc in API requests.

Best practice is:



Pre-process into a smaller set of spend-based factors.

Populate emission_factors table with EXIOBASE-derived records.



Code Sketch



import pymrio



exio = pymrio.parse_exiobase3(path="IOT_2020_pxp.zip")

exio.calc_all()



# Example: satellite account / final demand emissions

factors = exio.satellite.F_Y

# Then aggregate & export to CSV → ETL into emission_factors

Gotchas





Country codes may not be pure ISO; mapping is required.

Some sectors might legitimately have zero emissions; filter carefully.

Pre-calculation can take minutes; keep this out of request paths.







3. XBRL / XHTML Template Strategy



Date: 2024-11-30

Topic: Generating compliant XHTML/iXBRL



What I learned





Best practice: keep a canonical internal model of report data and map that into templates.

Templates should:



Be versioned (e.g. ESRS_E1_v1).

Have explicit tag mappings (concept → line item).

Be validated via an XHTML/iXBRL validator before sending to users.



High-Level Pattern



def generate_xhtml(report_data: ReportModel) -> str:

    """

    Takes internal report model, renders XHTML/iXBRL.

    """

    context = build_xbrl_context(report_data)

    return render_template("esrs_e1.xhtml.jinja2", **context)

Gotchas





Small mistakes in tags/contexts can invalidate the whole document.

Keep a tiny, known-good sample file for regression tests.







4. [Next Learning Here]



When you go deep on something (e.g. new regime, new library, non-trivial bug):





Add a new section: Topic, What I learned, Code pattern, Gotchas.

Reference relevant files (ETL scripts, services, tests).

