"""
Seed diverse sample upcoming bank auctions into Supabase across Tamil Nadu.
"""

from models.auction_schema import ExtractedAuctionProperty, AssetCategory, PossessionType, PropertyBoundaries
from database.supabase_client import AuctionDatabaseClient

def main():
    db = AuctionDatabaseClient()

    props = [
        ExtractedAuctionProperty(
            bank_name="Indian Overseas Bank",
            branch_name="Anna Nagar West Branch, Chennai",
            borrower_name="M/s. Sri Balaji Logistics & Traders",
            asset_category=AssetCategory.FLAT_APARTMENT,
            possession_type=PossessionType.PHYSICAL,
            survey_numbers=["T.S. No. 42/1", "Block 14"],
            patta_or_door_no="Flat No. 3A, 3rd Floor, Lotus Enclave",
            village_or_locality="Anna Nagar West",
            taluk="Aminjikarai",
            district="Chennai",
            state="Tamil Nadu",
            pincode="600040",
            area_description="3 BHK Luxury Flat measuring 1,650 Sq.ft super built-up area",
            area_sqft=1650.0,
            boundaries=PropertyBoundaries(
                north="30 feet Main Road",
                south="Flat No. 3B",
                east="Lift and Common Staircase",
                west="Compound Wall & Private Garden",
            ),
            reserve_price_inr=11500000,
            emd_amount_inr=1150000,
            bid_increment_inr=100000,
            emd_last_date="2026-12-14T17:00:00",
            inspection_date_info="10-12-2026 from 10:00 AM to 4:00 PM",
            auction_date="2026-12-16T11:00:00",
            authorized_officer_name="Chief Manager & Recovery Head",
            contact_phone="+91-44-26154000",
            bidding_portal_url="https://www.iob.in/Tender_Eauction",
        ),
        ExtractedAuctionProperty(
            bank_name="Canara Bank",
            branch_name="Madurai Main / ARMB Branch",
            borrower_name="Thiru. P. Sundaram",
            asset_category=AssetCategory.COMMERCIAL,
            possession_type=PossessionType.PHYSICAL,
            survey_numbers=["Town Survey No. 112/3B"],
            patta_or_door_no="Door No. 45/A, Bypass Road",
            village_or_locality="Ponmeni",
            taluk="Madurai South",
            district="Madurai",
            state="Tamil Nadu",
            pincode="625016",
            area_description="Commercial Showroom Building of 3,200 Sq.ft (Ground + 1st Floor)",
            area_sqft=3200.0,
            boundaries=PropertyBoundaries(
                north="Madurai-Theni National Highway",
                south="Private Residential Layout",
                east="Commercial Complex of Muthuvel",
                west="20 feet North-South Cross Road",
            ),
            reserve_price_inr=8200000,
            emd_amount_inr=820000,
            bid_increment_inr=50000,
            emd_last_date="2026-12-18T17:00:00",
            inspection_date_info="12-12-2026 to 15-12-2026 with prior appointment",
            auction_date="2026-12-20T10:30:00",
            authorized_officer_name="Assistant General Manager",
            contact_phone="+91-452-2348000",
            bidding_portal_url="https://canarabank.com/eauction",
        ),
        ExtractedAuctionProperty(
            bank_name="Bank of Baroda",
            branch_name="Textile Park Branch, Tiruppur",
            borrower_name="M/s. Tirupur Garments Export Pvt Ltd",
            asset_category=AssetCategory.INDUSTRIAL,
            possession_type=PossessionType.SYMBOLIC,
            survey_numbers=["S.F. No. 340/2", "341/1A"],
            patta_or_door_no="Plot No. 18 & 19, SIDCO Industrial Estate",
            village_or_locality="Mudalipalayam",
            taluk="Tiruppur South",
            district="Tiruppur",
            state="Tamil Nadu",
            pincode="641606",
            area_description="Industrial Land measuring 45 Cents with 15,000 Sq.ft RCC/Galvalume Shed",
            area_sqft=19602.0,
            boundaries=PropertyBoundaries(
                north="40 feet SIDCO Main Road",
                south="Substation & EB Transformer",
                east="Plot No. 20 (Dyeing Unit)",
                west="Plot No. 17 (Knitting Factory)",
            ),
            reserve_price_inr=24000000,
            emd_amount_inr=2400000,
            bid_increment_inr=200000,
            emd_last_date="2026-12-22T17:00:00",
            inspection_date_info="18-12-2026 from 11:00 AM to 3:00 PM",
            auction_date="2026-12-24T14:00:00",
            authorized_officer_name="Senior Manager (Recovery)",
            contact_phone="+91-421-2489000",
            bidding_portal_url="https://www.bankeauctions.com",
        ),
        ExtractedAuctionProperty(
            bank_name="Punjab National Bank",
            branch_name="Salem Junction Branch",
            borrower_name="Thiru. C. Subramani & Smt. S. Lakshmi",
            asset_category=AssetCategory.AGRICULTURAL,
            possession_type=PossessionType.PHYSICAL,
            survey_numbers=["R.S. No. 78/2B", "79/1"],
            patta_or_door_no="Patta No. 891",
            village_or_locality="Omalur",
            taluk="Omalur",
            district="Salem",
            state="Tamil Nadu",
            pincode="636455",
            area_description="Fertile Coconut and Mango Grove measuring 2 Acres 50 Cents with borewell and 5 HP pump set",
            area_sqft=108900.0,
            boundaries=PropertyBoundaries(
                north="Periya Kulam Channel / Cart Track",
                south="Land of Ramanathan",
                east="S.F. No. 78/2A Coconut Thoppu",
                west="Omalur-Mecheri Panchayat Road",
            ),
            reserve_price_inr=3500000,
            emd_amount_inr=350000,
            bid_increment_inr=50000,
            emd_last_date="2026-12-29T17:00:00",
            inspection_date_info="Direct site inspection permitted on 22-12-2026",
            auction_date="2026-12-31T11:00:00",
            authorized_officer_name="Chief Manager (Zonal Sastra)",
            contact_phone="+91-427-2341200",
            bidding_portal_url="https://baanknet.com",
        ),
    ]

    for p in props:
        r = db.upsert_property(p, source_portal="Bank Foreclosure Notice")
        event = r.get("auction_event_hash", "")[:12]
        print(f"Upserted: {p.bank_name} | {p.district} | {p.asset_category.value} | Event: {event}")

    print("All sample properties upserted successfully.")

if __name__ == "__main__":
    main()

