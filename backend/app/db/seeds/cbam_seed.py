# app/db/seeds/cbam_seed.py
"""
CBAM Reference Data Seed

Seeds cbam_products and cbam_factor_sources tables with V1 CN codes for:
- Iron/Steel: 7206-7229, 7301-7326
- Aluminium: 7601-7616
- Cement: 2523
- Fertilisers: 2808, 3102-3105
- Electricity: 2716
- Hydrogen: 2804

Also seeds default emission factors for each product category.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.cbam import (
    CBAMProduct,
    CBAMFactorSource,
    CBAMProductSector,
    CBAMFactorDataset,
)
from app.models.emission_factor import EmissionFactor

logger = logging.getLogger(__name__)


# =============================================================================
# CBAM PRODUCTS - V1 CN CODES
# =============================================================================

CBAM_PRODUCTS = [
    # Iron and Steel (Chapter 72: 7206-7229)
    {"cn_code": "72061000", "description": "Iron - primary forms", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720600", "unit": "tonne"},
    {"cn_code": "72071100", "description": "Semi-finished products of iron or non-alloy steel - <0.25% carbon, rectangular cross-section", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720700", "unit": "tonne"},
    {"cn_code": "72071200", "description": "Semi-finished products of iron or non-alloy steel - <0.25% carbon, other", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720700", "unit": "tonne"},
    {"cn_code": "72072000", "description": "Semi-finished products of iron or non-alloy steel - >=0.25% carbon", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720700", "unit": "tonne"},
    {"cn_code": "72081000", "description": "Flat-rolled products of iron, >=600mm wide, hot-rolled, not clad", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720800", "unit": "tonne"},
    {"cn_code": "72082500", "description": "Flat-rolled products of iron, hot-rolled, pickled, thickness >=4.75mm", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720800", "unit": "tonne"},
    {"cn_code": "72083600", "description": "Flat-rolled products of iron, hot-rolled, not pickled, thickness >10mm", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720800", "unit": "tonne"},
    {"cn_code": "72091500", "description": "Flat-rolled products of iron, cold-rolled, thickness >=3mm", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720900", "unit": "tonne"},
    {"cn_code": "72091600", "description": "Flat-rolled products of iron, cold-rolled, thickness >1mm to <3mm", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "720900", "unit": "tonne"},
    {"cn_code": "72101100", "description": "Flat-rolled products of iron, plated with tin, thickness >=0.5mm", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721000", "unit": "tonne"},
    {"cn_code": "72103000", "description": "Flat-rolled products of iron, electrolytically plated with zinc", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721000", "unit": "tonne"},
    {"cn_code": "72111300", "description": "Flat-rolled products of iron, <600mm wide, hot-rolled, >=4.75mm thick", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721100", "unit": "tonne"},
    {"cn_code": "72119000", "description": "Flat-rolled products of iron, <600mm wide, other", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721100", "unit": "tonne"},
    {"cn_code": "72131000", "description": "Bars and rods, hot-rolled, with indentations from rolling", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721300", "unit": "tonne"},
    {"cn_code": "72139100", "description": "Bars and rods, hot-rolled, circular cross-section, <14mm", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721300", "unit": "tonne"},
    {"cn_code": "72142000", "description": "Bars and rods, hot-rolled, with indentations from rolling (concrete reinforcing)", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721400", "unit": "tonne"},
    {"cn_code": "72149100", "description": "Bars and rods, hot-rolled, rectangular cross-section", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721400", "unit": "tonne"},
    {"cn_code": "72155000", "description": "Bars and rods, cold-formed or finished, other", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721500", "unit": "tonne"},
    {"cn_code": "72161000", "description": "Angles, shapes and sections of iron, U sections", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721600", "unit": "tonne"},
    {"cn_code": "72162100", "description": "Angles, shapes and sections of iron, L sections", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721600", "unit": "tonne"},
    {"cn_code": "72163100", "description": "Angles, shapes and sections of iron, U sections hot-rolled >=80mm", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721600", "unit": "tonne"},
    {"cn_code": "72171000", "description": "Wire of iron or non-alloy steel, not plated", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721700", "unit": "tonne"},
    {"cn_code": "72172000", "description": "Wire of iron or non-alloy steel, plated with zinc", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721700", "unit": "tonne"},
    {"cn_code": "72181000", "description": "Stainless steel ingots and other primary forms", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721800", "unit": "tonne"},
    {"cn_code": "72189100", "description": "Stainless steel semi-finished products, rectangular cross-section", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721800", "unit": "tonne"},
    {"cn_code": "72191100", "description": "Flat-rolled products of stainless steel, hot-rolled, >=600mm, >10mm thick", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721900", "unit": "tonne"},
    {"cn_code": "72193100", "description": "Flat-rolled products of stainless steel, cold-rolled, >=600mm, >=4.75mm thick", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "721900", "unit": "tonne"},
    {"cn_code": "72202000", "description": "Flat-rolled products of stainless steel, <600mm wide, cold-rolled", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722000", "unit": "tonne"},
    {"cn_code": "72210000", "description": "Bars and rods of stainless steel, hot-rolled", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722100", "unit": "tonne"},
    {"cn_code": "72221100", "description": "Bars and rods of stainless steel, cold-formed, circular cross-section", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722200", "unit": "tonne"},
    {"cn_code": "72224000", "description": "Angles, shapes and sections of stainless steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722200", "unit": "tonne"},
    {"cn_code": "72230000", "description": "Wire of stainless steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722300", "unit": "tonne"},
    {"cn_code": "72241000", "description": "Other alloy steel ingots and other primary forms", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722400", "unit": "tonne"},
    {"cn_code": "72249000", "description": "Other alloy steel semi-finished products", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722400", "unit": "tonne"},
    {"cn_code": "72251100", "description": "Flat-rolled products of silicon-electrical steel, grain-oriented", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722500", "unit": "tonne"},
    {"cn_code": "72254000", "description": "Flat-rolled products of other alloy steel, >=600mm wide, not further worked", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722500", "unit": "tonne"},
    {"cn_code": "72261100", "description": "Flat-rolled products of silicon-electrical steel, <600mm wide, grain-oriented", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722600", "unit": "tonne"},
    {"cn_code": "72262000", "description": "Flat-rolled products of high-speed steel, <600mm wide", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722600", "unit": "tonne"},
    {"cn_code": "72271000", "description": "Bars and rods of high-speed steel, hot-rolled", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722700", "unit": "tonne"},
    {"cn_code": "72279000", "description": "Bars and rods of other alloy steel, hot-rolled", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722700", "unit": "tonne"},
    {"cn_code": "72281000", "description": "Bars and rods of high-speed steel, cold-formed", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722800", "unit": "tonne"},
    {"cn_code": "72286000", "description": "Bars and rods of other alloy steel, cold-formed", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722800", "unit": "tonne"},
    {"cn_code": "72292000", "description": "Wire of silicon-manganese steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722900", "unit": "tonne"},
    {"cn_code": "72299000", "description": "Wire of other alloy steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "722900", "unit": "tonne"},

    # Iron and Steel articles (Chapter 73: 7301-7326)
    {"cn_code": "73011000", "description": "Sheet piling of iron or steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730100", "unit": "tonne"},
    {"cn_code": "73021000", "description": "Railway or tramway track construction material of iron or steel - rails", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730200", "unit": "tonne"},
    {"cn_code": "73030000", "description": "Tubes, pipes and hollow profiles, of cast iron", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730300", "unit": "tonne"},
    {"cn_code": "73041100", "description": "Line pipe for oil or gas pipelines, seamless, of stainless steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730400", "unit": "tonne"},
    {"cn_code": "73041900", "description": "Line pipe for oil or gas pipelines, seamless, other", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730400", "unit": "tonne"},
    {"cn_code": "73042200", "description": "Drill pipe, seamless, of stainless steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730400", "unit": "tonne"},
    {"cn_code": "73043100", "description": "Tubes and pipes, seamless, cold-drawn, of iron or non-alloy steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730400", "unit": "tonne"},
    {"cn_code": "73051100", "description": "Line pipe for oil or gas pipelines, longitudinally welded", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730500", "unit": "tonne"},
    {"cn_code": "73052000", "description": "Casing for drilling for oil or gas, welded", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730500", "unit": "tonne"},
    {"cn_code": "73061100", "description": "Line pipe for oil or gas pipelines, welded, of stainless steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730600", "unit": "tonne"},
    {"cn_code": "73063000", "description": "Tubes and pipes, welded, circular cross-section, of iron or non-alloy steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730600", "unit": "tonne"},
    {"cn_code": "73066100", "description": "Tubes and pipes, welded, square or rectangular cross-section", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730600", "unit": "tonne"},
    {"cn_code": "73071100", "description": "Tube or pipe fittings, cast, of non-malleable cast iron", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730700", "unit": "tonne"},
    {"cn_code": "73072100", "description": "Flanges, of stainless steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730700", "unit": "tonne"},
    {"cn_code": "73089000", "description": "Structures of iron or steel, other", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730800", "unit": "tonne"},
    {"cn_code": "73090000", "description": "Reservoirs, tanks, vats of iron or steel, >300L", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "730900", "unit": "tonne"},
    {"cn_code": "73101000", "description": "Tanks, casks, drums, 50-300L, of iron or steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "731000", "unit": "tonne"},
    {"cn_code": "73110000", "description": "Containers for compressed or liquefied gas, of iron or steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "731100", "unit": "tonne"},
    {"cn_code": "73181500", "description": "Screws and bolts, threaded, of iron or steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "731800", "unit": "tonne"},
    {"cn_code": "73182100", "description": "Spring washers of iron or steel", "sector": CBAMProductSector.IRON_STEEL, "hs_code": "731800", "unit": "tonne"},

    # Aluminium (Chapter 76: 7601-7616)
    {"cn_code": "76011000", "description": "Unwrought aluminium, not alloyed", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760100", "unit": "tonne"},
    {"cn_code": "76012000", "description": "Unwrought aluminium, alloyed", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760100", "unit": "tonne"},
    {"cn_code": "76020000", "description": "Aluminium waste and scrap", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760200", "unit": "tonne"},
    {"cn_code": "76031000", "description": "Aluminium powders of non-lamellar structure", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760300", "unit": "tonne"},
    {"cn_code": "76032000", "description": "Aluminium powders of lamellar structure; aluminium flakes", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760300", "unit": "tonne"},
    {"cn_code": "76041010", "description": "Aluminium bars, not alloyed", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760400", "unit": "tonne"},
    {"cn_code": "76041090", "description": "Aluminium profiles, not alloyed", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760400", "unit": "tonne"},
    {"cn_code": "76042100", "description": "Aluminium profiles, alloyed, hollow", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760400", "unit": "tonne"},
    {"cn_code": "76042910", "description": "Aluminium bars, alloyed", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760400", "unit": "tonne"},
    {"cn_code": "76042990", "description": "Aluminium profiles, alloyed, other", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760400", "unit": "tonne"},
    {"cn_code": "76051100", "description": "Aluminium wire, not alloyed, max cross-section >7mm", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760500", "unit": "tonne"},
    {"cn_code": "76051900", "description": "Aluminium wire, not alloyed, max cross-section <=7mm", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760500", "unit": "tonne"},
    {"cn_code": "76052100", "description": "Aluminium wire, alloyed, max cross-section >7mm", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760500", "unit": "tonne"},
    {"cn_code": "76052900", "description": "Aluminium wire, alloyed, max cross-section <=7mm", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760500", "unit": "tonne"},
    {"cn_code": "76061110", "description": "Aluminium plates, sheets and strip, not alloyed, rectangular, >0.2mm thick", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760600", "unit": "tonne"},
    {"cn_code": "76061191", "description": "Aluminium coils, not alloyed, >0.2mm thick, width >500mm", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760600", "unit": "tonne"},
    {"cn_code": "76061210", "description": "Aluminium plates, alloyed, rectangular, >0.2mm thick", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760600", "unit": "tonne"},
    {"cn_code": "76069100", "description": "Aluminium plates, not alloyed, other", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760600", "unit": "tonne"},
    {"cn_code": "76069200", "description": "Aluminium plates, alloyed, other", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760600", "unit": "tonne"},
    {"cn_code": "76071110", "description": "Aluminium foil, rolled, <=0.2mm, not backed", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760700", "unit": "tonne"},
    {"cn_code": "76071190", "description": "Aluminium foil, rolled, <=0.2mm, other", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760700", "unit": "tonne"},
    {"cn_code": "76072010", "description": "Aluminium foil, backed with paper", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760700", "unit": "tonne"},
    {"cn_code": "76072090", "description": "Aluminium foil, backed, other", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760700", "unit": "tonne"},
    {"cn_code": "76081000", "description": "Aluminium tubes and pipes, not alloyed", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760800", "unit": "tonne"},
    {"cn_code": "76082000", "description": "Aluminium tubes and pipes, alloyed", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760800", "unit": "tonne"},
    {"cn_code": "76090000", "description": "Aluminium tube or pipe fittings", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "760900", "unit": "tonne"},
    {"cn_code": "76101000", "description": "Aluminium doors, windows and their frames", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "761000", "unit": "tonne"},
    {"cn_code": "76109000", "description": "Aluminium structures (other than doors/windows)", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "761000", "unit": "tonne"},
    {"cn_code": "76110000", "description": "Aluminium reservoirs, tanks, vats >300L", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "761100", "unit": "tonne"},
    {"cn_code": "76121000", "description": "Collapsible tubular containers of aluminium", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "761200", "unit": "tonne"},
    {"cn_code": "76129010", "description": "Rigid tubular containers of aluminium, <50L", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "761200", "unit": "tonne"},
    {"cn_code": "76130000", "description": "Aluminium containers for compressed or liquefied gas", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "7613", "unit": "tonne"},
    {"cn_code": "76141000", "description": "Stranded wire, cables, plaited bands of aluminium, with steel core", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "7614", "unit": "tonne"},
    {"cn_code": "76149000", "description": "Stranded wire, cables, plaited bands of aluminium, without steel core", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "7614", "unit": "tonne"},
    {"cn_code": "76151000", "description": "Aluminium table, kitchen or household articles", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "7615", "unit": "tonne"},
    {"cn_code": "76152000", "description": "Aluminium sanitary ware", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "7615", "unit": "tonne"},
    {"cn_code": "76161000", "description": "Aluminium nails, tacks, staples, screws, bolts", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "761600", "unit": "tonne"},
    {"cn_code": "76169100", "description": "Aluminium cloth, grill, netting", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "761600", "unit": "tonne"},
    {"cn_code": "76169900", "description": "Other articles of aluminium", "sector": CBAMProductSector.ALUMINIUM, "hs_code": "761600", "unit": "tonne"},

    # Cement (Chapter 25: 2523)
    {"cn_code": "25231000", "description": "Cement clinkers", "sector": CBAMProductSector.CEMENT, "hs_code": "252300", "unit": "tonne"},
    {"cn_code": "25232100", "description": "White Portland cement, whether or not artificially coloured", "sector": CBAMProductSector.CEMENT, "hs_code": "252300", "unit": "tonne"},
    {"cn_code": "25232900", "description": "Other Portland cement", "sector": CBAMProductSector.CEMENT, "hs_code": "252300", "unit": "tonne"},
    {"cn_code": "25233000", "description": "Aluminous cement", "sector": CBAMProductSector.CEMENT, "hs_code": "252300", "unit": "tonne"},
    {"cn_code": "25239000", "description": "Other hydraulic cements", "sector": CBAMProductSector.CEMENT, "hs_code": "252300", "unit": "tonne"},

    # Fertilisers (Chapter 28: 2808 and Chapter 31: 3102-3105)
    {"cn_code": "28080000", "description": "Nitric acid; sulphonitric acids", "sector": CBAMProductSector.FERTILISERS, "hs_code": "280800", "unit": "tonne"},
    {"cn_code": "31021000", "description": "Urea, whether or not in aqueous solution", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31022100", "description": "Ammonium sulphate", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31022900", "description": "Double salts and mixtures of ammonium sulphate and ammonium nitrate", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31023000", "description": "Ammonium nitrate, whether or not in aqueous solution", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31024000", "description": "Mixtures of ammonium nitrate with calcium carbonate", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31025000", "description": "Sodium nitrate", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31026000", "description": "Double salts and mixtures of calcium nitrate and ammonium nitrate", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31028000", "description": "Mixtures of urea and ammonium nitrate in aqueous or ammoniacal solution", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31029000", "description": "Other mineral or chemical fertilisers, nitrogenous", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310200", "unit": "tonne"},
    {"cn_code": "31031100", "description": "Superphosphates containing by weight 35% or more of diphosphorus pentaoxide", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310300", "unit": "tonne"},
    {"cn_code": "31031900", "description": "Other superphosphates", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310300", "unit": "tonne"},
    {"cn_code": "31039000", "description": "Other mineral or chemical fertilisers, phosphatic", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310300", "unit": "tonne"},
    {"cn_code": "31042000", "description": "Potassium chloride", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310400", "unit": "tonne"},
    {"cn_code": "31043000", "description": "Potassium sulphate", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310400", "unit": "tonne"},
    {"cn_code": "31049000", "description": "Other mineral or chemical fertilisers, potassic", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310400", "unit": "tonne"},
    {"cn_code": "31051000", "description": "Goods in tablets or similar forms, or in packages <= 10kg gross weight", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310500", "unit": "tonne"},
    {"cn_code": "31052000", "description": "Mineral or chemical fertilisers containing N, P and K", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310500", "unit": "tonne"},
    {"cn_code": "31053000", "description": "Diammonium hydrogenorthophosphate (DAP)", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310500", "unit": "tonne"},
    {"cn_code": "31054000", "description": "Ammonium dihydrogenorthophosphate (MAP)", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310500", "unit": "tonne"},
    {"cn_code": "31055100", "description": "Fertilisers containing nitrates and phosphates", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310500", "unit": "tonne"},
    {"cn_code": "31055900", "description": "Other fertilisers containing N and P", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310500", "unit": "tonne"},
    {"cn_code": "31056000", "description": "Mineral or chemical fertilisers containing P and K", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310500", "unit": "tonne"},
    {"cn_code": "31059000", "description": "Other mineral or chemical fertilisers", "sector": CBAMProductSector.FERTILISERS, "hs_code": "310500", "unit": "tonne"},

    # Electricity (Chapter 27: 2716)
    {"cn_code": "27160000", "description": "Electrical energy", "sector": CBAMProductSector.ELECTRICITY, "hs_code": "271600", "unit": "MWh"},

    # Hydrogen (Chapter 28: 2804)
    {"cn_code": "28041000", "description": "Hydrogen", "sector": CBAMProductSector.HYDROGEN, "hs_code": "280400", "unit": "kg"},
]


# =============================================================================
# CBAM FACTOR SOURCES
# =============================================================================

CBAM_FACTOR_SOURCES = [
    {
        "dataset": CBAMFactorDataset.CBAM_DEFAULT,
        "version": "2024_Q1",
        "description": "EU CBAM Default Emission Factors - Official values from EU Commission implementing regulation",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956",
        "effective_date": datetime(2024, 1, 1),
    },
    {
        "dataset": CBAMFactorDataset.CBAM_DEFAULT,
        "version": "2023_TRANSITIONAL",
        "description": "EU CBAM Transitional Period Default Factors",
        "source_url": "https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en",
        "effective_date": datetime(2023, 10, 1),
        "expiry_date": datetime(2025, 12, 31),
    },
    {
        "dataset": CBAMFactorDataset.EXIOBASE_2020,
        "version": "3.8.2",
        "description": "EXIOBASE 3 Multi-Regional Input-Output Database - Spend-based emission factors",
        "source_url": "https://zenodo.org/record/5589597",
        "effective_date": datetime(2020, 1, 1),
    },
]


# =============================================================================
# DEFAULT EMISSION FACTORS FOR CBAM PRODUCTS
# =============================================================================

# EU default emission factors by sector (tCO2e per tonne unless otherwise noted)
# Source: EU CBAM Regulation implementing acts
CBAM_DEFAULT_FACTORS = [
    # Iron & Steel
    {
        "scope": "SCOPE_1",
        "category": "cbam_iron_steel",
        "activity_type": "crude_steel_production",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 1.85,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Iron and Steel",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_iron_steel",
        "activity_type": "hot_rolled_steel",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 1.95,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Iron and Steel",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_iron_steel",
        "activity_type": "cold_rolled_steel",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 2.10,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Iron and Steel",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_iron_steel",
        "activity_type": "stainless_steel",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 2.85,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Iron and Steel",
    },

    # Aluminium
    {
        "scope": "SCOPE_1",
        "category": "cbam_aluminium",
        "activity_type": "primary_aluminium",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 8.40,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Aluminium (primary)",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_aluminium",
        "activity_type": "secondary_aluminium",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.50,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Aluminium (secondary/recycled)",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_aluminium",
        "activity_type": "aluminium_products",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 6.80,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Aluminium products (average)",
    },

    # Cement
    {
        "scope": "SCOPE_1",
        "category": "cbam_cement",
        "activity_type": "cement_clinker",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.83,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Cement clinker",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_cement",
        "activity_type": "portland_cement",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.70,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Portland cement",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_cement",
        "activity_type": "blended_cement",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.55,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Blended cement",
    },

    # Fertilisers
    {
        "scope": "SCOPE_1",
        "category": "cbam_fertilisers",
        "activity_type": "ammonia",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 2.18,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Ammonia",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_fertilisers",
        "activity_type": "urea",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 2.65,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Urea",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_fertilisers",
        "activity_type": "ammonium_nitrate",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 3.90,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Ammonium nitrate",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_fertilisers",
        "activity_type": "nitric_acid",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 2.75,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Nitric acid",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_fertilisers",
        "activity_type": "mixed_fertilisers",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 1.50,
        "unit": "tCO2e/tonne",
        "source": "EU CBAM Default - Mixed fertilisers (NPK)",
    },

    # Electricity
    {
        "scope": "SCOPE_2",
        "category": "cbam_electricity",
        "activity_type": "grid_electricity",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.40,
        "unit": "tCO2e/MWh",
        "source": "EU CBAM Default - Electricity (global average)",
    },
    {
        "scope": "SCOPE_2",
        "category": "cbam_electricity",
        "activity_type": "grid_electricity",
        "country_code": "CN",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.58,
        "unit": "tCO2e/MWh",
        "source": "EU CBAM Default - Electricity (China)",
    },
    {
        "scope": "SCOPE_2",
        "category": "cbam_electricity",
        "activity_type": "grid_electricity",
        "country_code": "IN",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.72,
        "unit": "tCO2e/MWh",
        "source": "EU CBAM Default - Electricity (India)",
    },
    {
        "scope": "SCOPE_2",
        "category": "cbam_electricity",
        "activity_type": "grid_electricity",
        "country_code": "RU",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.45,
        "unit": "tCO2e/MWh",
        "source": "EU CBAM Default - Electricity (Russia)",
    },
    {
        "scope": "SCOPE_2",
        "category": "cbam_electricity",
        "activity_type": "grid_electricity",
        "country_code": "TR",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.43,
        "unit": "tCO2e/MWh",
        "source": "EU CBAM Default - Electricity (Turkey)",
    },

    # Hydrogen
    {
        "scope": "SCOPE_1",
        "category": "cbam_hydrogen",
        "activity_type": "grey_hydrogen",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 9.30,
        "unit": "kgCO2e/kg",
        "source": "EU CBAM Default - Hydrogen (SMR grey)",
    },
    {
        "scope": "SCOPE_1",
        "category": "cbam_hydrogen",
        "activity_type": "blue_hydrogen",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 4.50,
        "unit": "kgCO2e/kg",
        "source": "EU CBAM Default - Hydrogen (SMR with CCS)",
    },
    {
        "scope": "SCOPE_2",
        "category": "cbam_hydrogen",
        "activity_type": "green_hydrogen",
        "country_code": "GLOBAL",
        "year": 2024,
        "dataset": "CBAM_DEFAULT",
        "factor": 0.50,
        "unit": "kgCO2e/kg",
        "source": "EU CBAM Default - Hydrogen (electrolysis renewable)",
    },
]


def seed_cbam_products(db: Session) -> int:
    """
    Seed CBAM products table with V1 CN codes.

    Returns number of products inserted.
    """
    inserted = 0
    for product_data in CBAM_PRODUCTS:
        # Check if already exists
        existing = db.query(CBAMProduct).filter(
            CBAMProduct.cn_code == product_data["cn_code"]
        ).first()

        if not existing:
            product = CBAMProduct(
                cn_code=product_data["cn_code"],
                description=product_data["description"],
                sector=product_data["sector"],
                hs_code=product_data.get("hs_code"),
                unit=product_data.get("unit", "tonne"),
                is_active=True,
            )
            db.add(product)
            inserted += 1

    db.commit()
    logger.info(f"CBAM Products: Inserted {inserted} new products")
    return inserted


def seed_cbam_factor_sources(db: Session) -> int:
    """
    Seed CBAM factor sources table.

    Returns number of sources inserted.
    """
    inserted = 0
    for source_data in CBAM_FACTOR_SOURCES:
        # Check if already exists (by dataset + version)
        existing = db.query(CBAMFactorSource).filter(
            CBAMFactorSource.dataset == source_data["dataset"],
            CBAMFactorSource.version == source_data["version"]
        ).first()

        if not existing:
            source = CBAMFactorSource(
                dataset=source_data["dataset"],
                version=source_data["version"],
                description=source_data.get("description"),
                source_url=source_data.get("source_url"),
                effective_date=source_data.get("effective_date"),
                expiry_date=source_data.get("expiry_date"),
            )
            db.add(source)
            inserted += 1

    db.commit()
    logger.info(f"CBAM Factor Sources: Inserted {inserted} new sources")
    return inserted


def seed_cbam_emission_factors(db: Session) -> int:
    """
    Seed emission factors for CBAM products.

    Returns number of factors inserted.
    """
    inserted = 0
    for factor_data in CBAM_DEFAULT_FACTORS:
        # Check if already exists
        existing = db.query(EmissionFactor).filter(
            EmissionFactor.scope == factor_data["scope"],
            EmissionFactor.category == factor_data["category"],
            EmissionFactor.activity_type == factor_data["activity_type"],
            EmissionFactor.country_code == factor_data["country_code"],
            EmissionFactor.year == factor_data["year"],
            EmissionFactor.dataset == factor_data["dataset"],
        ).first()

        if not existing:
            factor = EmissionFactor(
                scope=factor_data["scope"],
                category=factor_data["category"],
                activity_type=factor_data["activity_type"],
                country_code=factor_data["country_code"],
                year=factor_data["year"],
                dataset=factor_data["dataset"],
                factor=factor_data["factor"],
                unit=factor_data["unit"],
                source=factor_data.get("source"),
                method="average_data",
                regulation="CBAM",
            )
            db.add(factor)
            inserted += 1

    db.commit()
    logger.info(f"CBAM Emission Factors: Inserted {inserted} new factors")
    return inserted


def run_cbam_seed(db: Session) -> dict:
    """
    Run all CBAM seed operations.

    Returns summary of inserted records.
    """
    logger.info("Starting CBAM seed...")

    products = seed_cbam_products(db)
    factor_sources = seed_cbam_factor_sources(db)
    emission_factors = seed_cbam_emission_factors(db)

    summary = {
        "cbam_products": products,
        "cbam_factor_sources": factor_sources,
        "cbam_emission_factors": emission_factors,
    }

    logger.info(f"CBAM seed complete: {summary}")
    return summary
