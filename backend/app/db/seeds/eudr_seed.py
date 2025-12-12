# app/db/seeds/eudr_seed.py
"""
EUDR Reference Data Seed

Seeds eudr_commodities table with the 7 EUDR-regulated commodities:
- Cattle (and derived: leather, beef)
- Cocoa (and derived: chocolate, cocoa butter)
- Coffee
- Palm oil (and derived: palm kernel, glycerol)
- Soy (and derived: soy cake, soy oil)
- Timber (and derived: wood products, pulp, paper)
- Rubber (and derived: tyres, rubber products)

Includes HS codes for each commodity and derivatives.
"""
import logging
from sqlalchemy.orm import Session

from app.models.eudr import (
    EUDRCommodity,
    EUDRCommodityType,
    EUDRRiskLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# EUDR COMMODITIES - 7 CORE CATEGORIES + DERIVATIVES
# =============================================================================

EUDR_COMMODITIES = [
    # =========================================================================
    # CATTLE
    # =========================================================================
    {
        "name": "cattle_live",
        "commodity_type": EUDRCommodityType.CATTLE,
        "description": "Live bovine animals",
        "hs_code": "0102",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Includes all live bovine animals for breeding, dairy, or slaughter",
    },
    {
        "name": "beef_fresh",
        "commodity_type": EUDRCommodityType.CATTLE,
        "description": "Meat of bovine animals, fresh or chilled",
        "hs_code": "0201",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Fresh beef and veal",
    },
    {
        "name": "beef_frozen",
        "commodity_type": EUDRCommodityType.CATTLE,
        "description": "Meat of bovine animals, frozen",
        "hs_code": "0202",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Frozen beef and veal",
    },
    {
        "name": "beef_offal",
        "commodity_type": EUDRCommodityType.CATTLE,
        "description": "Edible offal of bovine animals",
        "hs_code": "0206",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Edible offal from cattle",
    },
    {
        "name": "beef_prepared",
        "commodity_type": EUDRCommodityType.CATTLE,
        "description": "Prepared or preserved meat of bovine animals",
        "hs_code": "1602",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Corned beef, canned beef, etc.",
    },
    {
        "name": "leather_raw",
        "commodity_type": EUDRCommodityType.CATTLE,
        "description": "Raw hides and skins of bovine animals",
        "hs_code": "4101",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Untanned bovine hides",
    },
    {
        "name": "leather_tanned",
        "commodity_type": EUDRCommodityType.CATTLE,
        "description": "Tanned or crust hides and skins of bovine animals",
        "hs_code": "4104",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Processed bovine leather",
    },
    {
        "name": "leather_finished",
        "commodity_type": EUDRCommodityType.CATTLE,
        "description": "Finished leather of bovine animals",
        "hs_code": "4107",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Finished bovine leather for products",
    },

    # =========================================================================
    # COCOA
    # =========================================================================
    {
        "name": "cocoa_beans",
        "commodity_type": EUDRCommodityType.COCOA,
        "description": "Cocoa beans, whole or broken, raw or roasted",
        "hs_code": "1801",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Primary cocoa commodity from West Africa, Latin America",
    },
    {
        "name": "cocoa_shells",
        "commodity_type": EUDRCommodityType.COCOA,
        "description": "Cocoa shells, husks, skins and other cocoa waste",
        "hs_code": "1802",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Cocoa processing byproducts",
    },
    {
        "name": "cocoa_paste",
        "commodity_type": EUDRCommodityType.COCOA,
        "description": "Cocoa paste, whether or not defatted",
        "hs_code": "1803",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Cocoa liquor/mass for chocolate production",
    },
    {
        "name": "cocoa_butter",
        "commodity_type": EUDRCommodityType.COCOA,
        "description": "Cocoa butter, fat and oil",
        "hs_code": "1804",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Cocoa butter for chocolate and cosmetics",
    },
    {
        "name": "cocoa_powder",
        "commodity_type": EUDRCommodityType.COCOA,
        "description": "Cocoa powder, not containing added sugar",
        "hs_code": "1805",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Unsweetened cocoa powder",
    },
    {
        "name": "chocolate",
        "commodity_type": EUDRCommodityType.COCOA,
        "description": "Chocolate and other food preparations containing cocoa",
        "hs_code": "1806",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Chocolate bars, pralines, confectionery",
    },

    # =========================================================================
    # COFFEE
    # =========================================================================
    {
        "name": "coffee_green",
        "commodity_type": EUDRCommodityType.COFFEE,
        "description": "Coffee, not roasted, not decaffeinated",
        "hs_code": "090111",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Green coffee beans",
    },
    {
        "name": "coffee_green_decaf",
        "commodity_type": EUDRCommodityType.COFFEE,
        "description": "Coffee, not roasted, decaffeinated",
        "hs_code": "090112",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Decaffeinated green coffee beans",
    },
    {
        "name": "coffee_roasted",
        "commodity_type": EUDRCommodityType.COFFEE,
        "description": "Coffee, roasted, not decaffeinated",
        "hs_code": "090121",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Roasted coffee beans",
    },
    {
        "name": "coffee_roasted_decaf",
        "commodity_type": EUDRCommodityType.COFFEE,
        "description": "Coffee, roasted, decaffeinated",
        "hs_code": "090122",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Decaffeinated roasted coffee",
    },
    {
        "name": "coffee_husks_skins",
        "commodity_type": EUDRCommodityType.COFFEE,
        "description": "Coffee husks and skins; coffee substitutes containing coffee",
        "hs_code": "090190",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Coffee processing byproducts",
    },
    {
        "name": "coffee_extracts",
        "commodity_type": EUDRCommodityType.COFFEE,
        "description": "Extracts, essences and concentrates of coffee",
        "hs_code": "210111",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Instant coffee, coffee concentrates",
    },

    # =========================================================================
    # PALM OIL
    # =========================================================================
    {
        "name": "palm_oil_crude",
        "commodity_type": EUDRCommodityType.PALM_OIL,
        "description": "Palm oil, crude",
        "hs_code": "151110",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Crude palm oil (CPO) from oil palm fruit",
    },
    {
        "name": "palm_oil_refined",
        "commodity_type": EUDRCommodityType.PALM_OIL,
        "description": "Palm oil, refined but not chemically modified",
        "hs_code": "151190",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Refined palm oil (RBD)",
    },
    {
        "name": "palm_kernel_oil_crude",
        "commodity_type": EUDRCommodityType.PALM_OIL,
        "description": "Palm kernel oil, crude",
        "hs_code": "151321",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Crude palm kernel oil (CPKO)",
    },
    {
        "name": "palm_kernel_oil_refined",
        "commodity_type": EUDRCommodityType.PALM_OIL,
        "description": "Palm kernel oil, refined",
        "hs_code": "151329",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Refined palm kernel oil",
    },
    {
        "name": "palm_kernel_cake",
        "commodity_type": EUDRCommodityType.PALM_OIL,
        "description": "Palm kernel cake and other solid residues",
        "hs_code": "230660",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Palm kernel expeller (PKE) for animal feed",
    },
    {
        "name": "glycerol_palm",
        "commodity_type": EUDRCommodityType.PALM_OIL,
        "description": "Glycerol, crude; glycerol waters and lyes (from palm)",
        "hs_code": "1520",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Glycerol derived from palm oil processing",
    },
    {
        "name": "fatty_acids_palm",
        "commodity_type": EUDRCommodityType.PALM_OIL,
        "description": "Fatty acids from palm oil",
        "hs_code": "3823",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Industrial fatty acids from palm",
    },

    # =========================================================================
    # SOY
    # =========================================================================
    {
        "name": "soy_beans",
        "commodity_type": EUDRCommodityType.SOY,
        "description": "Soya beans, whether or not broken",
        "hs_code": "1201",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Raw soybeans for processing or direct use",
    },
    {
        "name": "soy_flour",
        "commodity_type": EUDRCommodityType.SOY,
        "description": "Soya bean flour and meal",
        "hs_code": "1208",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Soy flour for food products",
    },
    {
        "name": "soy_oil_crude",
        "commodity_type": EUDRCommodityType.SOY,
        "description": "Soya-bean oil, crude",
        "hs_code": "150710",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Crude soybean oil",
    },
    {
        "name": "soy_oil_refined",
        "commodity_type": EUDRCommodityType.SOY,
        "description": "Soya-bean oil, refined",
        "hs_code": "150790",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Refined soybean oil for food use",
    },
    {
        "name": "soy_cake",
        "commodity_type": EUDRCommodityType.SOY,
        "description": "Soya-bean oil-cake and other solid residues",
        "hs_code": "2304",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Soybean meal for animal feed - major driver of deforestation",
    },
    {
        "name": "soy_lecithin",
        "commodity_type": EUDRCommodityType.SOY,
        "description": "Lecithins derived from soya",
        "hs_code": "2923",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Soy lecithin for food and industrial use",
    },

    # =========================================================================
    # TIMBER
    # =========================================================================
    {
        "name": "timber_logs",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Wood in the rough, whether or not stripped of bark",
        "hs_code": "4403",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Raw logs, tropical and temperate hardwoods",
    },
    {
        "name": "timber_sawn",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Wood sawn or chipped lengthwise, thickness > 6mm",
        "hs_code": "4407",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Sawn timber, lumber, boards",
    },
    {
        "name": "timber_veneer",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Veneer sheets and sheets for plywood",
        "hs_code": "4408",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Wood veneer for furniture and panels",
    },
    {
        "name": "timber_plywood",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Plywood, veneered panels and similar laminated wood",
        "hs_code": "4412",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Plywood sheets and panels",
    },
    {
        "name": "timber_particle_board",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Particle board and similar board of wood",
        "hs_code": "4410",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Chipboard, OSB, MDF",
    },
    {
        "name": "timber_fibreboard",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Fibreboard of wood or other ligneous materials",
        "hs_code": "4411",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "MDF, HDF, hardboard",
    },
    {
        "name": "wood_charcoal",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Wood charcoal (including shell or nut charcoal)",
        "hs_code": "4402",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Charcoal from wood - often linked to illegal logging",
    },
    {
        "name": "wood_pulp",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Chemical wood pulp, dissolving grades",
        "hs_code": "4702",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Pulp for paper and cellulose products",
    },
    {
        "name": "paper_newsprint",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Newsprint, in rolls or sheets",
        "hs_code": "4801",
        "risk_profile_default": EUDRRiskLevel.LOW,
        "notes": "Newsprint paper",
    },
    {
        "name": "paper_uncoated",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Uncoated paper and paperboard",
        "hs_code": "4802",
        "risk_profile_default": EUDRRiskLevel.LOW,
        "notes": "Writing and printing paper",
    },
    {
        "name": "paper_packaging",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Paper and paperboard for packaging",
        "hs_code": "4804",
        "risk_profile_default": EUDRRiskLevel.LOW,
        "notes": "Kraft paper, containerboard",
    },
    {
        "name": "furniture_wood",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Wooden furniture",
        "hs_code": "9403",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Furniture made of wood",
    },
    {
        "name": "printed_books",
        "commodity_type": EUDRCommodityType.TIMBER,
        "description": "Printed books, brochures, leaflets",
        "hs_code": "4901",
        "risk_profile_default": EUDRRiskLevel.LOW,
        "notes": "Books and printed materials",
    },

    # =========================================================================
    # RUBBER
    # =========================================================================
    {
        "name": "rubber_natural",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "Natural rubber in primary forms or in plates, sheets or strip",
        "hs_code": "4001",
        "risk_profile_default": EUDRRiskLevel.HIGH,
        "notes": "Natural rubber latex and solid rubber",
    },
    {
        "name": "rubber_compounded",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "Compounded rubber, unvulcanised",
        "hs_code": "4005",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Rubber compounds for manufacturing",
    },
    {
        "name": "rubber_tubes",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "Tubes, pipes and hoses of vulcanised rubber",
        "hs_code": "4009",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Industrial rubber tubing",
    },
    {
        "name": "rubber_conveyor_belts",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "Conveyor or transmission belts of vulcanised rubber",
        "hs_code": "4010",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Industrial rubber belts",
    },
    {
        "name": "tyres_new",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "New pneumatic tyres of rubber",
        "hs_code": "4011",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "New tyres for vehicles",
    },
    {
        "name": "tyres_retreaded",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "Retreaded or used pneumatic tyres of rubber",
        "hs_code": "4012",
        "risk_profile_default": EUDRRiskLevel.LOW,
        "notes": "Retreaded and used tyres",
    },
    {
        "name": "rubber_gaskets",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "Gaskets, washers and other seals of vulcanised rubber",
        "hs_code": "4016",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Rubber sealing products",
    },
    {
        "name": "rubber_gloves",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "Gloves, mittens and mitts of vulcanised rubber",
        "hs_code": "401511",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Surgical and industrial rubber gloves",
    },
    {
        "name": "rubber_footwear",
        "commodity_type": EUDRCommodityType.RUBBER,
        "description": "Footwear with outer soles and uppers of rubber",
        "hs_code": "6401",
        "risk_profile_default": EUDRRiskLevel.MEDIUM,
        "notes": "Rubber boots and shoes",
    },
]


def seed_eudr_commodities(db: Session) -> int:
    """
    Seed EUDR commodities table with the 7 regulated commodities and derivatives.

    Returns number of commodities inserted.
    """
    inserted = 0
    for commodity_data in EUDR_COMMODITIES:
        # Check if already exists
        existing = db.query(EUDRCommodity).filter(
            EUDRCommodity.name == commodity_data["name"]
        ).first()

        if not existing:
            commodity = EUDRCommodity(
                name=commodity_data["name"],
                commodity_type=commodity_data["commodity_type"],
                description=commodity_data.get("description"),
                hs_code=commodity_data.get("hs_code"),
                risk_profile_default=commodity_data.get("risk_profile_default", EUDRRiskLevel.MEDIUM),
                notes=commodity_data.get("notes"),
                is_active=True,
            )
            db.add(commodity)
            inserted += 1

    db.commit()
    logger.info(f"EUDR Commodities: Inserted {inserted} new commodities")
    return inserted


def run_eudr_seed(db: Session) -> dict:
    """
    Run all EUDR seed operations.

    Returns summary of inserted records.
    """
    logger.info("Starting EUDR seed...")

    commodities = seed_eudr_commodities(db)

    summary = {
        "eudr_commodities": commodities,
    }

    logger.info(f"EUDR seed complete: {summary}")
    return summary
