# Week 19 Compliance Rules

The compliance checker uses configurable local validation rules for common construction document types.

## Checked Items

- Required metadata
- Mandatory document sections
- Revision information
- Submission or document date
- Document number or reference number
- Signature information
- Approval information
- Basic inconsistency checks

## Supported Document Types

- Drawing
- Specification
- Method Statement
- Material Submittal
- Shop Drawing
- Inspection Report
- Contract
- Meeting Minutes
- RFI

## Compliance Scoring

The score starts at 100. Failed rules deduct points based on severity:

- Critical: 18 points
- High: 12 points
- Medium: 7 points
- Low: 3 points

## Status Levels

- Compliant: score 85 or above
- Needs Revision: score 60 to 84
- Non-Compliant: score below 60
