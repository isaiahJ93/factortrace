# Read the current file and fix it
with open('xpath31/crypto/production_signer.py', 'r') as f:
    lines = f.readlines()

# Find where imports end
import_end = 0
for i, line in enumerate(lines):
    if line.strip() and not line.startswith(('import', 'from', '#')) and 'logger =' not in line:
        import_end = i
        break

# Create fixed version
fixed_lines = lines[:import_end]
fixed_lines.append('\nclass ProductionSigner:\n')
fixed_lines.append('    """Production digital signature system with full eIDAS compliance."""\n')
fixed_lines.append('    \n')
fixed_lines.append('    EU_LOTL_URL = "https://ec.europa.eu/tools/lotl/eu-lotl.xml"\n')
fixed_lines.append('    TSA_ENDPOINTS = [{"name": "DigiCert", "url": "http://timestamp.digicert.com", "backup_url": "http://timestamp.digicert.com", "root_cert": "DigiCert"}]\n')
fixed_lines.append('    TSL_NS = {"tsl": "http://uri.etsi.org/02231/v2#", "ds": "http://www.w3.org/2000/09/xmldsig#", "xades": "http://uri.etsi.org/01903/v1.3.2#"}\n')
fixed_lines.append('    \n')

# Indent all methods
for line in lines[import_end:]:
    if line.strip():
        fixed_lines.append('    ' + line)
    else:
        fixed_lines.append(line)

# Write fixed version
with open('xpath31/crypto/production_signer_fixed.py', 'w') as f:
    f.writelines(fixed_lines)
    
print("Fixed version created at xpath31/crypto/production_signer_fixed.py")
