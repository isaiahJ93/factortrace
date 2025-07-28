# xpath31/cli.py - Enhanced CLI with quantum migration info
"""Command-line interface for XPath31 ESRS validator."""
import click
import json
import sys
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime

from .validator import XBRLValidator
from .crypto.production_signer import ProductionSigner
from .clients.esap_client import ESAPClient

logger = logging.getLogger(__name__)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-critical output')
@click.pass_context
def cli(ctx, verbose, quiet):
    """XPath31 ESRS XBRL/iXBRL validator and toolkit."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)
        
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet

@cli.command()
@click.argument('filing', type=click.Path(exists=True))
@click.option('--rules', '-r', multiple=True, help='Specific rules to apply')
@click.option('--output', '-o', type=click.Choice(['json', 'text', 'html']), default='text')
@click.option('--strict', is_flag=True, help='Fail on warnings')
def validate(filing, rules, output, strict):
    """Validate an XBRL/iXBRL filing."""
    validator = XBRLValidator()
    
    try:
        with open(filing, 'rb') as f:
            results = validator.validate(f.read(), rules=list(rules) if rules else None)
            
        if output == 'json':
            click.echo(json.dumps(results, indent=2))
        elif output == 'html':
            # Generate HTML report
            html = validator.generate_html_report(results)
            click.echo(html)
        else:
            # Text output
            for result in results['validation_results']:
                level = click.style(result['severity'], 
                                  fg='red' if result['severity'] == 'ERROR' else 'yellow')
                click.echo(f"{level}: {result['message']} [{result['rule_id']}]")
                if result.get('line'):
                    click.echo(f"  Line: {result['line']}")
                if result.get('element'):
                    click.echo(f"  Element: {result['element']}")
                    
        # Exit code
        has_errors = any(r['severity'] == 'ERROR' for r in results['validation_results'])
        has_warnings = any(r['severity'] == 'WARNING' for r in results['validation_results'])
        
        if has_errors:
            sys.exit(1)
        elif strict and has_warnings:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

@cli.command()
@click.argument('filing', type=click.Path(exists=True))
@click.option('--key', type=click.Path(exists=True), help='Private key file')
@click.option('--cert', type=click.Path(exists=True), help='Certificate file')
@click.option('--output', '-o', type=click.Path(), help='Output signature file')
def sign(filing, key, cert, output):
    """Sign an XBRL/iXBRL filing."""
    try:
        if key and cert:
            signer = ProductionSigner(
                private_key_path=Path(key),
                certificate_path=Path(cert)
            )
        else:
            # Development mode
            import os
            os.environ['DEVELOPMENT_MODE'] = 'true'
            signer = ProductionSigner()
            
        with open(filing, 'rb') as f:
            content = f.read()
            
        metadata = {
            'filename': Path(filing).name,
            'size': len(content),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        signature = signer.sign_filing(content, metadata)
        
        if output:
            with open(output, 'w') as f:
                json.dump(signature, f, indent=2)
            click.echo(f"Signature saved to {output}")
        else:
            click.echo(json.dumps(signature, indent=2))
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

@cli.command('quantum-plan')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
def quantum_plan(as_json):
    """Display quantum-safe migration plan."""
    try:
        # Use development mode to avoid key requirements
        import os
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        signer = ProductionSigner()
        plan = signer.prepare_quantum_migration()
        
        if as_json:
            click.echo(json.dumps(plan, indent=2))
        else:
            click.echo("=== XPath31 Quantum-Safe Migration Plan ===\n")
            click.echo(f"Current Algorithm: {plan['current_algorithm']}")
            click.echo(f"Target Algorithm: {plan['migration_path']}\n")
            
            click.echo("Implementation Status:")
            for key, value in plan['implementation_status'].items():
                click.echo(f"  {key}: {value}")
                
            click.echo("\nTimeline:")
            for phase, description in plan['timeline'].items():
                click.echo(f"  {phase}: {description}")
                
            click.echo("\nRequirements:")
            for i, req in enumerate(plan['requirements'], 1):
                click.echo(f"  {i}. {req}")
                
            click.echo("\nReferences:")
            for lib, url in plan['libraries'].items():
                click.echo(f"  {lib}: {url}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

@cli.command()
@click.argument('filing', type=click.Path(exists=True))
@click.option('--endpoint', help='ESAP endpoint URL')
@click.option('--token', help='Authentication token')
@click.option('--tenant', help='Tenant identifier')
def submit(filing, endpoint, token, tenant):
    """Submit filing to ESAP."""
    try:
        client = ESAPClient(
            base_url=endpoint or "https://api.esap.europa.eu",
            auth_token=token or os.environ.get('ESAP_TOKEN')
        )
        
        with open(filing, 'rb') as f:
            content = f.read()
            
        result = client.submit_filing(
            filing_content=content,
            filename=Path(filing).name,
            tenant_id=tenant
        )
        
        click.echo(f"Submission ID: {result['submission_id']}")
        click.echo(f"Status: {result['status']}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

@cli.group()
def tools():
    """Additional tools and utilities."""
    pass

@tools.command('check-cert')
@click.argument('cert_file', type=click.Path(exists=True))
def check_cert(cert_file):
    """Check if certificate is eIDAS qualified."""
    try:
        with open(cert_file, 'rb') as f:
            cert_data = f.read()
            
        cert = load_pem_x509_certificate(cert_data, default_backend())
        
        click.echo(f"Subject: {cert.subject.rfc4514_string()}")
        click.echo(f"Issuer: {cert.issuer.rfc4514_string()}")
        click.echo(f"Valid from: {cert.not_valid_before}")
        click.echo(f"Valid to: {cert.not_valid_after}")
        
        # Check for eIDAS indicators
        qc_statements = False
        for ext in cert.extensions:
            if ext.oid._dotted_string == '1.3.6.1.5.5.7.1.3':  # qcStatements
                qc_statements = True
                break
                
        if qc_statements:
            click.echo(click.style("✓ Certificate appears to be eIDAS qualified", fg='green'))
        else:
            click.echo(click.style("✗ Certificate lacks eIDAS qcStatements", fg='yellow'))
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

if __name__ == '__main__':
    cli()
@cli.command('auto-tag')
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output iXBRL file')
@click.option('--format', type=click.Choice(['text', 'html']), default='text')
def auto_tag(input_file, output, format):
    """Auto-tag document with ESRS concepts."""
    from .taxonomy.taxonomy_loader import ESRSTaxonomyLoader
    from .tagging.auto_tagger import ESRSAutoTagger
    
    # Load content
    with open(input_file, 'r') as f:
        content = f.read()
        
    # Auto-tag
    tagger = ESRSAutoTagger()
    results = tagger.auto_tag_document(content, format=format)
    
    click.echo(f"Found {len(results)} taggable items")
    
    # Generate iXBRL
    ixbrl = tagger.generate_ixbrl(results)
    
    if output:
        with open(output, 'w') as f:
            f.write(ixbrl)
        click.echo(f"Generated {output}")
    else:
        click.echo(ixbrl)

@cli.command('auto-tag')
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output iXBRL file')
@click.option('--format', type=click.Choice(['text', 'html']), default='text')
def auto_tag(input_file, output, format):
    """Auto-tag document with ESRS concepts."""
    from .taxonomy.taxonomy_loader import ESRSTaxonomyLoader
    from .tagging.auto_tagger import ESRSAutoTagger
    
    # Load content
    with open(input_file, 'r') as f:
        content = f.read()
        
    # Auto-tag
    tagger = ESRSAutoTagger()
    results = tagger.auto_tag_document(content, format=format)
    
    click.echo(f"Found {len(results)} taggable items")
    
    if results:
        # Generate iXBRL
        ixbrl = tagger.generate_ixbrl(results)
        
        if output:
            with open(output, 'w') as f:
                f.write(ixbrl)
            click.echo(f"Generated {output}")
        else:
            click.echo(ixbrl)
    else:
        click.echo("No taggable items found")

@cli.command('auto-tag')
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output iXBRL file')
@click.option('--format', type=click.Choice(['text', 'html']), default='text')
def auto_tag(input_file, output, format):
    """Auto-tag document with ESRS concepts."""
    from .taxonomy.taxonomy_loader import ESRSTaxonomyLoader
    from .tagging.auto_tagger import ESRSAutoTagger
    
    # Load content
    with open(input_file, 'r') as f:
        content = f.read()
        
    # Auto-tag
    tagger = ESRSAutoTagger()
    results = tagger.auto_tag_document(content, format=format)
    
    click.echo(f"Found {len(results)} taggable items")
    
    if results:
        # Generate iXBRL
        ixbrl = tagger.generate_ixbrl(results)
        
        if output:
            with open(output, 'w') as f:
                f.write(ixbrl)
            click.echo(f"Generated {output}")
        else:
            click.echo(ixbrl)
    else:
        click.echo("No taggable items found")
