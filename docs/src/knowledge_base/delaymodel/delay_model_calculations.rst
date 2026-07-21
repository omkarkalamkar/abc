.. _delay_model_calculations:

========================
Delay Model Calculations
========================

The Telescope Monitoring and Control (TMC) sub-system is responsible for
the calculation and distribution of the delay model to the Mid.CBF, throughout the execution of an observation on the
SKA-Mid telescope.

For SKA-Mid, the delay model expresses the time offset that Mid.CBF must
apply to the digitised signal from each configured receptor (dish) so
that the signals from all receptors in a subarray are coherently aligned
on the requested sky target. The model accounts for:

* The *geometric delay* resulting from the different positions of the
  receptors relative to a common reference location on the site and the direction of the source on the
  celestial sphere.
* The *atmospheric delay* (troposphere) at the site, derived from local
  weather data (pressure, temperature and relative humidity).
* The *fixed instrumental delays* per receptor, obtained from the SKA
  Telescope Model (Telmodel) layout and applied so that each receptor's
  signal-chain length is corrected. The horizontal component is added
  to the constant term of the polynomial for that receptor, while the
  difference between the vertical and horizontal fixed delays is
  published as ``ypol_offset_ns``. This handling is consistent with
  **ADR-96**, which requires Mid.CBF to receive a per-receptor
  Y-polarisation constant delay offset in addition to the per-receptor
  delay polynomial, so that any static X/Y polarisation delay
  difference intrinsic to the receiver chain is corrected after Mid.CBF
  evaluates the polynomial.

Delay calculations are performed independently for each subarray and
published on the CSP Subarray Leaf Node's ``delayModel`` attribute. In
the TMC architecture, the **CSP Subarray Leaf Node (Mid)** owns the
delay-model lifecycle for its subarray. Calculations run on a dedicated
worker thread inside the CSP Subarray Leaf Node process. The thread is
started as part of processing the ``Configure`` command and stopped when
the observation ends (``End`` / ``Abort``; ``Restart`` stops it
transitively via ``Abort``).


Inputs to the delay computation
===============================

The delay-model calculation combines information from several sources
that are gathered by the CSP Subarray Leaf Node component manager:

* **Assigned receptors** — the list of dishes (for example ``SKA001`` …
  ``SKA133`` and ``MKT000`` … ``MKT063``) allocated to the subarray as
  a result of the ``AssignResources`` command.
* **Target pointing information** — obtained from the ``pointing``
  block of the ``Configure`` JSON. TMC supports the reference frames
  defined by **ADR-63** (``icrs``, ``altaz``, ``galactic``, ``special``
  and ``tle``); the corresponding ``katpoint.Target`` object is built
  from the ``field`` entry within each ``pointing.groups`` element.
* **Array layout** — fetched from Telmodel using the ``TelmodelSource``
  and ``TelmodelPath`` device properties. For each receptor the layout
  provides the WGS84 geodetic position (``lat``, ``lon``, ``h``), the
  dish diameter, the ``station_label`` (used as the *receptor*
  identifier throughout the delay model), and two fixed-delay entries
  — ``FIX_H`` and ``FIX_V`` — each expressed either as an equivalent
  cable length in metres (``units: "m"``) or as a time in seconds
  (``units: "s"``).
* **Reference location** — the layout entry labelled ``AC`` provides the
  WGS84 coordinates used as the common phase-centre reference for the
  ``katpoint.DelayCorrection`` object.
* **Weather data** — pressure (hPa), temperature (°C) and relative
  humidity, consumed by the ``katpoint`` refraction model to compute
  the wet atmospheric contribution. When a live weather-station device
  is configured through the ``WeatherStationDevName`` device property,
  its attributes are subscribed to; if the property is empty or the
  subscription fails, safe fallback value is used.


Delay-model calculation
=======================

For each configured target, the CSP Subarray Leaf Node instantiates a
``katpoint.DelayCorrection`` object whose antennas are the assigned
receptors and whose reference is the ``AC`` location described above.
On every cadence cycle the leaf node performs the following steps:

#. Computes six delay samples per receptor at timestamps
   :math:`t_0 + k \cdot T_v` for :math:`k \in \{-2, -1, 0, 1, 2, 3\}`,
   where :math:`T_v` is ``DelayValidityPeriod``. The reference time
   :math:`t_0` (``start_time_for_delay_calculation``) is initialised to
   ``datetime.today() + DelayModelTimeInAdvance`` when ``Configure``
   is processed, and is advanced by ``DelayCadence`` on each subsequent
   cycle, so that a fresh model is always available to Mid.CBF before
   its validity begins.
#. Requests the H (horizontal) and V (vertical) delay corrections from
   ``katpoint`` for each timestamp, using the current weather data.
   No additional per-target correction is applied at present
   (``extra_correction`` is fixed at ``0 s``).
#. For each receptor, fits a **fifth-order polynomial** in time to the
   H delay samples using ``numpy.polynomial.Polynomial.fit``. The
   coefficients returned by ``katpoint`` are in seconds and are
   converted to nanoseconds (multiplied by :math:`10^{9}`) before
   publication as ``xypol_coeffs_ns``. A polynomial is also fit
   internally to the V samples for symmetry, but its coefficients are
   *not* published: the runtime H/V variation is small enough that a
   single scalar offset per receptor per validity interval is
   sufficient (**ADR-96**).
#. Adds the fixed horizontal delay ``FIX_H`` to the constant term
   :math:`c_0` of the polynomial for the corresponding receptor.
   Telmodel entries expressed in seconds are first converted to an
   equivalent cable length in metres by multiplying with
   ``katpoint.delay_model.FIXEDSPEED``; the metre value is then
   converted to a time delay in nanoseconds via
   :math:`L / (0.7 \cdot c) \cdot 10^{9}`, where the factor ``0.7`` is
   the fibre propagation velocity relative to the speed of light in
   vacuum.
#. Computes the constant Y-vs-X polarisation offset ``ypol_offset_ns``
   as the ``FIX_V - FIX_H`` cable-length delay difference, converted to
   nanoseconds using the same factor.
#. Assembles the JSON payload described in :ref:`delay_model_format`
   and publishes it on the ``delayModel`` Tango attribute.

The delay evaluated at time :math:`t` (seconds since
``start_validity_sec``) is:

.. math::

   d(t) = c_0 + c_1 t + c_2 t^{2} + c_3 t^{3} + c_4 t^{4} + c_5 t^{5}

where :math:`c_0 \dots c_5` are the six entries of ``xypol_coeffs_ns``,
:math:`c_0` is in nanoseconds and :math:`c_k` is in
:math:`\text{ns} / \text{s}^{k}`. The same polynomial is applied to
both the X and Y polarisations; the Y polarisation is additionally
shifted by ``ypol_offset_ns`` at all times.


Timing and cadence
==================

The lifecycle of the delay model is driven by three configurable
device properties on the CSP Subarray Leaf Node (Mid) device:

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Property
     - Default values (seconds)
     - Meaning
   * - ``DelayModelTimeInAdvance``
     - ``30`` seconds
     - How far ahead of *now* the ``start_validity_sec`` of the first
       polynomial is placed. Gives Mid.CBF a margin to receive and
       load the new model before it becomes valid.
   * - ``DelayCadence``
     - ``10.0`` seconds
     - Period between consecutive publications of the ``delayModel``
       attribute. Also reported in the payload as ``cadence_sec`` so
       that Mid.CBF knows when to expect the next update.
   * - ``DelayValidityPeriod``
     - ``20.0`` seconds
     - Maximum time for which a published polynomial remains valid,
       reported as ``validity_period_sec``. Also used as the spacing
       :math:`T_v` between the six fit samples. If Mid.CBF does not
       receive a new model within this interval it flags an error
       and stops processing.

Values are configurable at deployment time via the ``values.yaml`` of
the ``ska-tmc-mid`` Helm chart. Refer to the
:ref:`Deployment <deployment>` section for details.

If the calculation of a polynomial cannot be completed before its
scheduled publication time, the delay-model thread logs a
``"Missed %d polynomials."`` warning, skips the missed slots and
resumes on the next aligned cadence boundary.


End-to-end flow
===============

The lifecycle of the delay model for a single scan is:

#. **Configure** — the CSP Subarray Leaf Node parses the ``pointing``
   block of the ``Configure`` JSON, constructs the ``katpoint.Target``
   object for each pointing group, and fetches the receptor layout
   from Telmodel. It creates one ``katpoint.DelayCorrection`` object
   per target using the assigned receptors, and starts the delay-model thread.
#. **Ongoing scan** — every ``DelayCadence`` seconds the delay-model
   thread computes a new polynomial, populates the JSON payload,
   updates the ``delayModel`` attribute and pushes change / archive
   events. Mid.CBF subscribes to these events and applies the model
   at the specified ``start_validity_sec``.
#. **End / Abort (/ Restart)** — the delay-model thread is stopped,
   the component manager's ``receptors_target_obj`` and
   ``delay_correction_objects`` maps are cleared, and the
   ``delayModel`` attribute is reset to its initial sentinel value.
   ``Restart`` triggers this path transitively through ``Abort``.

If a delay-calculation cycle fails, an error string is written to the
``delayModelError`` Tango attribute and the health state of the delay
sub-component is set to ``FAULT``, so that the CSP Subarray Leaf Node's
aggregated health state reports the failure to consumers.


.. _delay_model_format:

Delay-model format
==================

The delay model is provided as a JSON string. Its primary consumer is
Mid.CBF, but any client that needs to monitor or record it can
subscribe to the change events of the ``delayModel`` Tango attribute
on ``mid-tmc/subarray-leaf-node-csp/<subarray_id>``.

The payload conforms to the CSP Mid Delay Model schema, version 3.0
(fixed by the ``MID_DELAYMODEL_VERSION`` constant in
``ska_tmc_cspsubarrayleafnode.const``):

.. jsonschema:: https://schema.skao.int/ska-mid-csp-delaymodel/3.0
   :lift_definitions:
   :auto_reference:

Top-level fields:

* ``interface`` — URI of the JSON schema
  (``ska-mid-csp-delaymodel/3.0``).
* ``start_validity_sec`` — time at which Mid.CBF shall start applying
  the model, expressed as seconds since the SKA epoch
  (``1999-12-31T23:59:28`` UTC, TAI-referenced).
* ``cadence_sec`` — nominal interval between successive delay models.
* ``validity_period_sec`` — maximum period for which the model remains
  valid after ``start_validity_sec``.
* ``config_id`` — configuration ID of the current scan (from the
  ``common.config_id`` field of the ``Configure`` JSON), used by
  Mid.CBF to discard stale models from a previous observation.
* ``subarray`` — identifier of the subarray to which the model
  applies (1 – 16).
* ``receptor_delays`` — array of per-receptor delay descriptors:

  * ``receptor`` — the receptor (dish) identifier, for example
    ``SKA001`` or ``MKT000``.
  * ``xypol_coeffs_ns`` — six coefficients of the fifth-order
    polynomial that models the delay in nanoseconds; the same
    polynomial is applied to both the X and Y polarisations. Note
    that :math:`c_0` is dominated by the fixed cable delay
    (``FIX_H``) folded in during calculation, so its magnitude can
    be large (of order 10\ :sup:`3` ns).
  * ``ypol_offset_ns`` — constant delay offset of the Y polarisation
    with respect to the X polarisation, in nanoseconds.

The following example shows a delay-model payload published on the
``delayModel`` attribute for a three-receptor subarray:

.. literalinclude:: examples/receptor_delay_model.json
   :language: json
   :linenos:
