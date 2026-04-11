"""QAReport generation and verdict logic.

Produces a QAReport conforming to src/schemas/qa_report.schema.json.
Verdict rules:
  - 'fail': any finding with severity 'error'
  - 'pass_with_warnings': no errors, but warnings exist
  - 'pass': no errors, no warnings (info findings are OK)
"""

from datetime import datetime, timezone


def compute_verdict(findings, config=None):
    """Compute pass/pass_with_warnings/fail from findings list."""
    errors = sum(1 for f in findings if f['severity'] == 'error')
    warnings = sum(1 for f in findings if f['severity'] == 'warning')

    if errors > 0:
        return 'fail'
    elif warnings > 0:
        return 'pass_with_warnings'
    else:
        return 'pass'


def generate_report(findings, pptx_path, total_slides):
    """Generate a complete QAReport dict."""
    errors = sum(1 for f in findings if f['severity'] == 'error')
    warnings = sum(1 for f in findings if f['severity'] == 'warning')
    info = sum(1 for f in findings if f['severity'] == 'info')

    return {
        'inspected_at': datetime.now(timezone.utc).isoformat(),
        'pptx_path': pptx_path,
        'verdict': compute_verdict(findings),
        'summary': {
            'total_slides': total_slides,
            'errors': errors,
            'warnings': warnings,
            'info': info,
        },
        'findings': findings,
    }
