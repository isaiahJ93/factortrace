#!/bin/bash
# Complete ESRS Auto-tagging Script

INPUT_FILE="$1"
OUTPUT_FILE="${2:-tagged_output.xml}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

# Initialize XBRL output
cat > "$OUTPUT_FILE" << 'HEADER'
<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:esrs="https://xbrl.efrag.org/taxonomy/2023-12-31/esrs"
      xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
      xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
      xmlns:xlink="http://www.w3.org/1999/xlink">
  
  <!-- Contexts -->
  <xbrli:context id="c2024">
    <xbrli:entity>
      <xbrli:identifier scheme="http://www.example.com">COMPANY-001</xbrli:identifier>
    </xbrli:entity>
    <xbrli:period>
      <xbrli:instant>2024-12-31</xbrli:instant>
    </xbrli:period>
  </xbrli:context>
  
  <!-- Units -->
  <xbrli:unit id="EUR">
    <xbrli:measure>iso4217:EUR</xbrli:measure>
  </xbrli:unit>
  
  <xbrli:unit id="tCO2e">
    <xbrli:measure>esrs:tonnesCO2e</xbrli:measure>
  </xbrli:unit>
  
  <xbrli:unit id="MWh">
    <xbrli:measure>esrs:MegawattHour</xbrli:measure>
  </xbrli:unit>
  
  <xbrli:unit id="m3">
    <xbrli:measure>esrs:CubicMetre</xbrli:measure>
  </xbrli:unit>
  
  <xbrli:unit id="tonnes">
    <xbrli:measure>esrs:Tonne</xbrli:measure>
  </xbrli:unit>
  
  <xbrli:unit id="pure">
    <xbrli:measure>xbrli:pure</xbrli:measure>
  </xbrli:unit>
  
  <!-- Facts -->
HEADER

echo "Processing: $INPUT_FILE"
echo "Tagging ESRS concepts..."

# Function to extract and tag values
tag_value() {
    local pattern="$1"
    local concept="$2"
    local unit="$3"
    local decimals="${4:-0}"
    
    if grep -qiE "$pattern" "$INPUT_FILE"; then
        line=$(grep -iE "$pattern" "$INPUT_FILE" | head -1)
        value=$(echo "$line" | sed 's/.*: *//' | grep -oE '[0-9,]+(\.[0-9]+)?%?' | head -1)
        
        if [ -n "$value" ]; then
            # Add fact to XBRL
            if [ "$unit" = "pure" ] && [[ "$value" == *"%" ]]; then
                # Handle percentages
                value=$(echo "$value" | tr -d '%')
                echo "  <esrs:$concept contextRef='c2024' unitRef='pure' decimals='$decimals'>${value}</esrs:$concept>" >> "$OUTPUT_FILE"
            else
                echo "  <esrs:$concept contextRef='c2024' unitRef='$unit' decimals='$decimals'>${value}</esrs:$concept>" >> "$OUTPUT_FILE"
            fi
            echo "✓ Tagged: $concept = $value"
        fi
    fi
}

# Process ESRS E1 - Climate Change
echo "Processing ESRS E1 - Climate Change..."
tag_value "scope.*1.*emissions?" "GrossScope1GHGEmissions" "tCO2e" "0"
tag_value "scope.*2.*market.*based" "GrossScope2MarketBased" "tCO2e" "0"
tag_value "scope.*3.*total" "GrossScope3TotalEmissions" "tCO2e" "0"
tag_value "total.*GHG.*emissions?" "TotalGHGEmissions" "tCO2e" "0"
tag_value "renewable.*energy.*%" "RenewableEnergyPercentage" "pure" "1"
tag_value "energy.*consumption" "TotalEnergyConsumption" "MWh" "0"
tag_value "purchased.*goods.*services" "Scope3Category1PurchasedGoods" "tCO2e" "0"
tag_value "capital.*goods" "Scope3Category2CapitalGoods" "tCO2e" "0"

# Process ESRS E2 - Pollution
echo "Processing ESRS E2 - Pollution..."
tag_value "air.*pollutants?" "AirPollutants" "tonnes" "1"
tag_value "NOx.*emissions?" "NOxEmissions" "tonnes" "1"
tag_value "SOx.*emissions?" "SOxEmissions" "tonnes" "1"

# Process ESRS E3 - Water
echo "Processing ESRS E3 - Water..."
tag_value "water.*consumption" "TotalWaterConsumption" "m3" "0"
tag_value "water.*withdrawal" "WaterWithdrawal" "m3" "0"
tag_value "water.*intensity" "WaterIntensity" "m3" "2"

# Process ESRS E4 - Biodiversity
echo "Processing ESRS E4 - Biodiversity..."
tag_value "protected.*areas?" "ProtectedAreasImpacted" "hectares" "0"
tag_value "land.*use.*change" "LandUseChange" "hectares" "0"

# Process ESRS E5 - Circular Economy
echo "Processing ESRS E5 - Resource Use..."
tag_value "waste.*generated" "WasteGenerated" "tonnes" "0"
tag_value "waste.*recycled" "WasteRecycled" "tonnes" "0"
tag_value "recycling.*rate.*%" "WasteRecyclingRate" "pure" "1"
tag_value "hazardous.*waste" "HazardousWaste" "tonnes" "0"

# Process ESRS S1 - Own Workforce
echo "Processing ESRS S1 - Own Workforce..."
tag_value "total.*employees?" "TotalEmployees" "pure" "0"
tag_value "(?:female|women).*employees?.*%" "GenderDiversityAllEmployees" "pure" "1"
tag_value "gender.*pay.*gap" "GenderPayGap" "pure" "1"
tag_value "training.*hours?" "AverageTrainingHours" "hours" "1"
tag_value "(?:LTIFR|injury.*rate)" "WorkRelatedInjuries" "pure" "2"
tag_value "turnover.*rate" "EmployeeTurnoverRate" "pure" "1"

# Process ESRS G1 - Business Conduct
echo "Processing ESRS G1 - Business Conduct..."
tag_value "corruption.*incidents?" "ConfirmedIncidentsOfCorruption" "pure" "0"
tag_value "political.*contributions?" "PoliticalContributions" "EUR" "0"
tag_value "lobbying.*expenditure" "LobbyingExpenditure" "EUR" "0"
tag_value "whistleblow.*cases?" "WhistleblowingCases" "pure" "0"

# Process Financial Data
echo "Processing Financial Data..."
tag_value "revenue" "Revenue" "EUR" "-6"
tag_value "total.*assets?" "TotalAssets" "EUR" "-9"
tag_value "net.*profit" "NetProfit" "EUR" "-6"

# Close XBRL document
echo "</xbrl>" >> "$OUTPUT_FILE"

echo "✓ Auto-tagging complete: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "1. Convert to iXBRL: ./xpath31/scripts/ixbrl_formatter.sh $OUTPUT_FILE output.xhtml"
echo "2. Validate: xmllint --schema esrs-2023.xsd $OUTPUT_FILE"
