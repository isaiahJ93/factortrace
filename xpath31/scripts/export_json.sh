#!/bin/bash
# Export XBRL to JSON format

INPUT_FILE="$1"
OUTPUT_FILE="${2:-output.json}"

echo "Converting XBRL to JSON..."

# Convert XBRL to JSON using Python
python3 - "$INPUT_FILE" "$OUTPUT_FILE" << 'PYTHON'
import sys
import json
import xml.etree.ElementTree as ET
from datetime import datetime

input_file = sys.argv[1]
output_file = sys.argv[2]

# Parse XBRL
tree = ET.parse(input_file)
root = tree.getroot()

# Extract all facts
facts = {}
contexts = {}
units = {}

# Get contexts
for context in root.findall('.//{http://www.xbrl.org/2003/instance}context'):
    context_id = context.get('id')
    entity = context.find('.//{http://www.xbrl.org/2003/instance}identifier')
    period = context.find('.//{http://www.xbrl.org/2003/instance}instant')
    if period is None:
        period = context.find('.//{http://www.xbrl.org/2003/instance}endDate')
    
    contexts[context_id] = {
        'entity': entity.text if entity is not None else None,
        'period': period.text if period is not None else None
    }

# Get units
for unit in root.findall('.//{http://www.xbrl.org/2003/instance}unit'):
    unit_id = unit.get('id')
    measure = unit.find('.//{http://www.xbrl.org/2003/instance}measure')
    units[unit_id] = measure.text if measure is not None else unit_id

# Extract facts
for elem in root.iter():
    if '}' in elem.tag and elem.text and elem.text.strip():
        concept = elem.tag.split('}')[1]
        if concept not in ['context', 'unit', 'xbrl', 'schemaRef']:
            context_ref = elem.get('contextRef', 'default')
            unit_ref = elem.get('unitRef', 'pure')
            
            facts[concept] = {
                'value': elem.text.strip(),
                'unit': units.get(unit_ref, unit_ref),
                'context': contexts.get(context_ref, {'period': '2024-12-31'}),
                'decimals': elem.get('decimals', '0')
            }

# Create structured JSON output
output = {
    'report': {
        'type': 'ESRS Sustainability Report',
        'created': datetime.now().isoformat(),
        'standard': 'EFRAG ESRS 2023'
    },
    'company': {
        'identifier': contexts.get('c2024', {}).get('entity', 'COMPANY-001'),
        'reporting_period': '2024'
    },
    'metrics': {
        'climate': {
            'emissions': {
                'scope1': facts.get('GrossScope1GHGEmissions', {}),
                'scope2_market': facts.get('GrossScope2MarketBased', {}),
                'scope3': facts.get('GrossScope3TotalEmissions', {}),
                'total': facts.get('TotalGHGEmissions', {})
            },
            'energy': {
                'renewable_percentage': facts.get('RenewableEnergyPercentage', {}),
                'total_consumption': facts.get('TotalEnergyConsumption', {})
            }
        },
        'environmental': {
            'water': {
                'consumption': facts.get('TotalWaterConsumption', {}),
                'intensity': facts.get('WaterIntensity', {})
            },
            'waste': {
                'generated': facts.get('WasteGenerated', {}),
                'recycled': facts.get('WasteRecycled', {}),
                'recycling_rate': facts.get('WasteRecyclingRate', {})
            }
        },
        'social': {
            'workforce': {
                'total_employees': facts.get('TotalEmployees', {}),
                'gender_diversity': facts.get('GenderDiversityAllEmployees', {}),
                'training_hours': facts.get('AverageTrainingHours', {}),
                'injury_rate': facts.get('WorkRelatedInjuries', {})
            }
        },
        'governance': {
            'business_conduct': {
                'corruption_incidents': facts.get('ConfirmedIncidentsOfCorruption', {}),
                'political_contributions': facts.get('PoliticalContributions', {})
            }
        }
    },
    'raw_facts': facts
}

# Write JSON
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f"✓ JSON export created: {output_file}")
PYTHON
