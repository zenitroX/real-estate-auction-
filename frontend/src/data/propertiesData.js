// Helper to build stable Unsplash image URLs
export function unsplash(id, w = 900) {
  return `https://images.unsplash.com/${id}?auto=format&fit=crop&w=${w}&q=75`;
}

// Shared interior / secondary shots used inside galleries
export const GALLERY_POOL = [
  unsplash('photo-1600607687939-ce8a6c25118c'), // modern living room
  unsplash('photo-1554995207-c18c203602cb'),    // bright interior
  unsplash('photo-1600121848594-d8644e57abab'), // luxury interior
  unsplash('photo-1584622650111-993a426fbf0a'), // bathroom
  unsplash('photo-1600566752355-35792bedcfea'), // kitchen / dining
  unsplash('photo-1600585154526-990dced4db0d'), // bedroom
  unsplash('photo-1512917774080-9991f1c4c750'), // luxury facade
  unsplash('photo-1600596542815-ffad4c1539a9'), // balcony / deck
];

// 14 Core Properties across Chennai, Bengaluru, Hyderabad, Delhi
export const RAW_PROPERTIES = [
  {
    id: 'p1',
    title: 'Independent House (3 BHK)',
    badge: 'BANK AUCTION',
    type: 'residential',
    locality: 'Madipakkam, Chennai',
    address: 'Plot No. 42, 2nd Main Road, Madipakkam, Chennai – 600091',
    bank: 'Canara Bank',
    branch: 'Santhome, Chennai',
    assetCode: 'CBCHN10246',
    contact: '044 - 2465 8700',
    officer: 'R. Meenakshi · +91 91760 11223',
    reserve: 7800000,
    increment: 50000,
    emdPct: 10,
    area: 2100,
    landArea: 1800,
    beds: 3,
    baths: 2,
    daysAhead: 2.26, // ~2d 6h 14m matching screenshot
    featured: true,
    images: [
      unsplash('photo-1600585154340-be6161a56a0c'),
      GALLERY_POOL[0],
      GALLERY_POOL[1],
      GALLERY_POOL[4],
      GALLERY_POOL[2],
      GALLERY_POOL[3],
    ],
    desc: 'Well-maintained independent duplex villa in the heart of Madipakkam with excellent connectivity to Velachery MRTS and OMR IT corridor. Clean title, SARFAESI bank-owned asset ready for immediate physical possession.'
  },
  {
    id: 'p2',
    title: 'Luxury Villa (4 BHK)',
    badge: 'E-AUCTION',
    type: 'residential',
    locality: 'Thoraipakkam, OMR, Chennai',
    address: 'Villa 14, Prestige Silver Springs, OMR, Chennai – 600097',
    bank: 'SBI',
    branch: 'Sholinganallur, Chennai',
    assetCode: 'SBCHN45782',
    contact: '044 - 2455 1190',
    officer: 'S. Ramanathan · +91 98401 55678',
    reserve: 14500000,
    increment: 100000,
    emdPct: 10,
    area: 3400,
    landArea: 2600,
    beds: 4,
    baths: 4,
    daysAhead: 3.43, // ~3d 10h 20m
    featured: true,
    images: [
      unsplash('photo-1613490493576-7fde63acd811'),
      GALLERY_POOL[2],
      GALLERY_POOL[0],
      GALLERY_POOL[5],
      GALLERY_POOL[6],
    ],
    desc: 'Premium gated-community luxury villa on OMR with private landscaped lawn, clubhouse privileges, 100% power backup and 2 covered car parks. High rental yield asset adjacent to major IT parks.'
  },
  {
    id: 'p3',
    title: 'Apartment (2 BHK)',
    badge: 'E-AUCTION',
    type: 'residential',
    locality: 'Velachery, Chennai',
    address: 'Block B-402, Lakeview Towers, Velachery, Chennai – 600042',
    bank: 'ICICI Bank',
    branch: 'Velachery, Chennai',
    assetCode: 'ICCHN20911',
    contact: '044 - 3020 7788',
    officer: 'K. Vignesh · +91 94440 22331',
    reserve: 5200000,
    increment: 25000,
    emdPct: 10,
    area: 1120,
    landArea: null,
    beds: 2,
    baths: 2,
    daysAhead: 3.43,
    featured: true,
    images: [
      unsplash('photo-1545324418-cc1a3fa10c00'),
      GALLERY_POOL[1],
      GALLERY_POOL[3],
      GALLERY_POOL[4],
    ],
    desc: 'Modern 2 BHK residential apartment on 4th floor with lift access, covered reserved parking, 24x7 security, and gym. 5 minutes drive from Phoenix MarketCity and Velachery railway station.'
  },
  {
    id: 'p4',
    title: 'Residential Plot',
    badge: 'BANK AUCTION',
    type: 'land',
    locality: 'Tambaram, Chennai',
    address: 'Survey No. 118/2, Tambaram West, Chennai – 600045',
    bank: 'SBI',
    branch: 'Tambaram, Chennai',
    assetCode: 'SBCHN51102',
    contact: '044 - 2496 2210',
    officer: 'A. Joseph · +91 98840 99881',
    reserve: 3600000,
    increment: 50000,
    emdPct: 10,
    area: null,
    landArea: 2400,
    beds: null,
    baths: null,
    daysAhead: 5.17, // ~5d 4h 08m
    featured: true,
    images: [
      unsplash('photo-1500382017468-9049fed7470f'),
      GALLERY_POOL[5],
      GALLERY_POOL[2],
    ],
    desc: 'CMDA approved rectangular East-facing residential land parcel with 40-foot blacktop road frontage, ground water source, and instant EB connection availability. Ready for immediate construction.'
  },
  {
    id: 'p5',
    title: 'Commercial Building',
    badge: 'E-AUCTION',
    type: 'commercial',
    locality: 'T. Nagar, Chennai',
    address: '72 Usman Road, T. Nagar, Chennai – 600017',
    bank: 'Canara Bank',
    branch: 'T. Nagar, Chennai',
    assetCode: 'CBCHN40795',
    contact: '044 - 2815 6630',
    officer: 'M. Sundaram · +91 97909 33445',
    reserve: 32000000,
    increment: 200000,
    emdPct: 10,
    area: 5800,
    landArea: 3200,
    beds: null,
    baths: 4,
    daysAhead: 6.06, // ~6d 1h 30m
    featured: true,
    images: [
      unsplash('photo-1486406146926-c627a92ad1ab'),
      GALLERY_POOL[1],
      GALLERY_POOL[0],
    ],
    desc: 'G+3 standalone commercial corporate building in the heart of T. Nagar shopping district. Central air-conditioning ducting, high footfall showcase frontage, and basement vehicle parking.'
  },
  {
    id: 'p6',
    title: 'Factory / Industrial Shed',
    badge: 'BANK AUCTION',
    type: 'industrial',
    locality: 'Sriperumbudur, Chennai',
    address: 'SIPCOT Industrial Park Phase-2, Sriperumbudur – 602105',
    bank: 'ICICI Bank',
    branch: 'Sriperumbudur, Chennai',
    assetCode: 'ICCHN61233',
    contact: '044 - 4012 9050',
    officer: 'P. Dinesh · +91 99620 44556',
    reserve: 47500000,
    increment: 250000,
    emdPct: 10,
    area: 14500,
    landArea: 22000,
    beds: null,
    baths: 3,
    daysAhead: 7.34, // ~7d 8h 12m
    featured: true,
    images: [
      unsplash('photo-1553413077-190dd305871c'),
      GALLERY_POOL[2],
      GALLERY_POOL[1],
    ],
    desc: 'Heavy industrial pre-engineered building (PEB) shed with 28 ft clear ridge height, 10-tonne EOT crane gantry, dedicated 250 KVA transformer yard, and wide truck maneuvering apron.'
  },
  {
    id: 'p7',
    title: 'Agriculture Land (3.5 Acres)',
    badge: 'E-AUCTION',
    type: 'land',
    locality: 'Kanchipuram, Tamil Nadu',
    address: 'Walajabad Road, Kanchipuram District – 631502',
    bank: 'Axis Bank',
    branch: 'Kanchipuram, Tamil Nadu',
    assetCode: 'AXKAN18402',
    contact: '044 - 2722 3410',
    officer: 'V. Natarajan · +91 94433 11890',
    reserve: 11000000,
    increment: 50000,
    emdPct: 10,
    area: null,
    landArea: 152460, // 3.5 acres in sqft
    beds: null,
    baths: null,
    daysAhead: 8.84, // ~8d 20h 15m
    featured: false,
    images: [
      unsplash('photo-1500595046743-cd271d694d30'),
      GALLERY_POOL[5],
      GALLERY_POOL[3],
    ],
    desc: 'Fertile agricultural land parcel with sweet-water borewell, free agricultural EB line, fully fenced perimeter and tar road frontage. Suitable for farmhouse, organic farming or agro-processing.'
  },
  {
    id: 'p8',
    title: '3 BHK High-Rise Apartment',
    badge: 'BANK AUCTION',
    type: 'residential',
    locality: 'Whitefield, Bengaluru',
    address: 'Prestige Boulevard, ITPL Main Road, Whitefield, Bengaluru – 560066',
    bank: 'SBI',
    branch: 'Whitefield, Bengaluru',
    assetCode: 'SBBLR33218',
    contact: '080 - 6180 4422',
    officer: 'S. Kulkarni · +91 98450 77123',
    reserve: 9200000,
    increment: 50000,
    emdPct: 10,
    area: 1780,
    landArea: null,
    beds: 3,
    baths: 3,
    daysAhead: 4.8,
    featured: true,
    images: [
      unsplash('photo-1460317442991-0ec209397118'),
      GALLERY_POOL[4],
      GALLERY_POOL[3],
      GALLERY_POOL[0],
    ],
    desc: 'Spacious East-facing 3 BHK in a tier-1 gated society with panoramic balcony view, infinity swimming pool, tennis court, and clubhouse. Located 5 minutes from Whitefield Metro Station.'
  },
  {
    id: 'p9',
    title: 'Commercial Retail Showroom',
    badge: 'E-AUCTION',
    type: 'commercial',
    locality: 'Banjara Hills, Hyderabad',
    address: 'Road No. 12, Banjara Hills, Hyderabad – 500034',
    bank: 'Canara Bank',
    branch: 'Banjara Hills, Hyderabad',
    assetCode: 'CBHYD77410',
    contact: '040 - 2354 8890',
    officer: 'T. Rao · +91 98480 33210',
    reserve: 18500000,
    increment: 150000,
    emdPct: 10,
    area: 3800,
    landArea: 4200,
    beds: null,
    baths: 2,
    daysAhead: 7.2,
    featured: false,
    images: [
      unsplash('photo-1441986300917-64674bd600d8'),
      GALLERY_POOL[1],
      GALLERY_POOL[2],
    ],
    desc: 'Double-height commercial showroom space on prime Banjara Hills thoroughfare. High visibility glass elevation, dedicated customer parking, and brand signage rights.'
  },
  {
    id: 'p10',
    title: 'Prime Residential Plot',
    badge: 'BANK AUCTION',
    type: 'land',
    locality: 'Gachibowli, Hyderabad',
    address: 'Financial District Outer Ring Road corridor, Gachibowli – 500032',
    bank: 'Canara Bank',
    branch: 'Gachibowli, Hyderabad',
    assetCode: 'CBHYD18340',
    contact: '040 - 2318 7712',
    officer: 'C. Srinivas · +91 99890 66543',
    reserve: 12000000,
    increment: 100000,
    emdPct: 10,
    area: null,
    landArea: 1800,
    beds: null,
    baths: null,
    daysAhead: 9.5,
    featured: false,
    images: [
      unsplash('photo-1470071459604-3b5ec3a7fe05'),
      GALLERY_POOL[5],
      GALLERY_POOL[0],
    ],
    desc: 'HMDA approved prime residential plot inside prestigious gated township, located adjacent to major multinational IT campus hubs. All infrastructure underground.'
  },
  {
    id: 'p11',
    title: 'Sea-Facing Luxury Apartment',
    badge: 'E-AUCTION',
    type: 'residential',
    locality: 'ECR, Chennai',
    address: 'East Coast Road, Akkarai Beach, Chennai – 600115',
    bank: 'ICICI Bank',
    branch: 'Adyar, Chennai',
    assetCode: 'ICCHN58201',
    contact: '044 - 2445 3360',
    officer: 'B. Karthik · +91 98410 88291',
    reserve: 11000000,
    increment: 75000,
    emdPct: 10,
    area: 1950,
    landArea: null,
    beds: 3,
    baths: 3,
    daysAhead: 5.7,
    featured: true,
    images: [
      unsplash('photo-1600596542815-ffad4c1539a9'),
      GALLERY_POOL[0],
      GALLERY_POOL[5],
      GALLERY_POOL[4],
    ],
    desc: 'Unobstructed Bay of Bengal sea views from every room. Gated oceanfront condominium featuring beach access, gym, power backup, and round-the-clock concierge service.'
  },
  {
    id: 'p12',
    title: 'Industrial Manufacturing Unit',
    badge: 'BANK AUCTION',
    type: 'industrial',
    locality: 'Peenya Industrial Area, Bengaluru',
    address: 'Plot 48, 2nd Stage, Peenya Industrial Area, Bengaluru – 560058',
    bank: 'SBI',
    branch: 'Peenya, Bengaluru',
    assetCode: 'SBBLR29561',
    contact: '080 - 2295 3341',
    officer: 'H. Manjunath · +91 94480 55112',
    reserve: 27500000,
    increment: 200000,
    emdPct: 10,
    area: 9800,
    landArea: 14000,
    beds: null,
    baths: 3,
    daysAhead: 11.3,
    featured: false,
    images: [
      unsplash('photo-1581094794329-c8112a89af12'),
      GALLERY_POOL[2],
      GALLERY_POOL[1],
    ],
    desc: 'Fully established light manufacturing machine shop with heavy power supply (350 HP), administrative building, testing lab room, and safe fire-suppression equipment.'
  },
  {
    id: 'p13',
    title: 'Commercial Office Tower Floor',
    badge: 'E-AUCTION',
    type: 'commercial',
    locality: 'Nehru Place, New Delhi',
    address: 'Level 5, Eros Corporate Tower, Nehru Place, New Delhi – 110019',
    bank: 'SBI',
    branch: 'Nehru Place, New Delhi',
    assetCode: 'SBDEL90227',
    contact: '011 - 4155 9080',
    officer: 'R. Sharma · +91 98110 44219',
    reserve: 42000000,
    increment: 500000,
    emdPct: 10,
    area: 7400,
    landArea: null,
    beds: null,
    baths: 4,
    daysAhead: 6.9,
    featured: false,
    images: [
      unsplash('photo-1497366216548-37526070297c'),
      GALLERY_POOL[1],
      GALLERY_POOL[0],
    ],
    desc: 'Furnished A-grade commercial floor in New Delhi corporate district with central HVAC, high-speed elevators, conference suites, cafeteria and 10 dedicated basement parking slots.'
  },
  {
    id: 'p14',
    title: '3 BHK Premium Flat',
    badge: 'BANK AUCTION',
    type: 'residential',
    locality: 'Nungambakkam, Chennai',
    address: 'Nungambakkam High Road, Chennai – 600034',
    bank: 'Canara Bank',
    branch: 'Nungambakkam, Chennai',
    assetCode: 'CBCHN33509',
    contact: '044 - 2822 5170',
    officer: 'S. Balaji · +91 98402 77610',
    reserve: 13500000,
    increment: 100000,
    emdPct: 10,
    area: 1920,
    landArea: null,
    beds: 3,
    baths: 3,
    daysAhead: 4.1,
    featured: true,
    images: [
      unsplash('photo-1600047509807-ba8f99d2cdde'),
      GALLERY_POOL[4],
      GALLERY_POOL[2],
      GALLERY_POOL[3],
    ],
    desc: 'Vaastu-compliant ultra-luxurious apartment in central Chennai CBD with Italian marble flooring, 2 covered car parks, video door security and clubhouse.'
  }
];

// Initial unverified scraped items ready for Admin review
export const UNVERIFIED_SCRAPED_PROPERTIES = [
  {
    id: 'scrape-101',
    title: 'Commercial Office Space (3,200 sq.ft)',
    badge: 'NEW NOTICE',
    type: 'commercial',
    locality: 'Guindy Industrial Estate, Chennai',
    address: 'SIDCO Industrial Estate, Guindy, Chennai – 600032',
    bank: 'State Bank of India',
    branch: 'Stressed Assets Recovery Branch (SARB), Egmore',
    assetCode: 'SBCHEG8831',
    contact: '1800 - 202 - SKANDX',
    officer: 'Authorized Officer · SBI SARB',
    reserve: 18500000,
    increment: 100000,
    emdPct: 10,
    area: 3200,
    landArea: null,
    beds: null,
    baths: 2,
    daysAhead: 14.5,
    featured: false,
    verified: false,
    status: 'PENDING_REVIEW',
    sourcePortal: 'IBAPI / e-Bikray Scraper',
    scrapedAt: '12 mins ago',
    ocrConfidence: '98.4%',
    images: [
      unsplash('photo-1497366216548-37526070297c'),
      GALLERY_POOL[0],
      GALLERY_POOL[1]
    ],
    desc: 'RAW SCRAPED: Commercial building floor under SARFAESI Act, 2002. Borrower: M/s Apex Tech Logistics Pvt Ltd. Clear physical possession stated in paper notice published in Indian Express.'
  },
  {
    id: 'scrape-102',
    title: 'Residential Duplex Plot (2,150 sq.ft)',
    badge: 'NEW NOTICE',
    type: 'land',
    locality: 'Porur, Chennai',
    address: 'Survey No. 240/1B, Mugalivakkam Main Road, Porur – 600125',
    bank: 'Canara Bank',
    branch: 'Asset Recovery Management Branch (ARMB)',
    assetCode: 'CBCHPOR4412',
    contact: '1800 - 202 - SKANDX',
    officer: 'Recovery Manager · Canara Bank',
    reserve: 6400000,
    increment: 50000,
    emdPct: 10,
    area: null,
    landArea: 2150,
    beds: null,
    baths: null,
    daysAhead: 18.2,
    featured: false,
    verified: false,
    status: 'PENDING_REVIEW',
    sourcePortal: 'Baanknet Crawler',
    scrapedAt: '35 mins ago',
    ocrConfidence: '96.8%',
    images: [
      unsplash('photo-1500382017468-9049fed7470f'),
      GALLERY_POOL[2]
    ],
    desc: 'RAW SCRAPED: Approved residential plot in developing residential layout. Encumbrance cert issued by Sub-Registrar Alandur. E-auction date scheduled for next month.'
  },
  {
    id: 'scrape-103',
    title: 'Light Engineering Shed / Industrial Warehouse',
    badge: 'NEW NOTICE',
    type: 'industrial',
    locality: 'Maraimalai Nagar, Chennai',
    address: 'Plot No. 18, Industrial Estate, Maraimalai Nagar – 603209',
    bank: 'Indian Bank',
    branch: 'Stressed Assets Management Branch',
    assetCode: 'IBCHMAR9012',
    contact: '1800 - 202 - SKANDX',
    officer: 'Chief Manager · Indian Bank',
    reserve: 29000000,
    increment: 200000,
    emdPct: 10,
    area: 8400,
    landArea: 12000,
    beds: null,
    baths: 2,
    daysAhead: 21.0,
    featured: false,
    verified: false,
    status: 'PENDING_REVIEW',
    sourcePortal: 'Gemini Vision OCR / Dinamalar Scanned Ad',
    scrapedAt: '1 hour ago',
    ocrConfidence: '99.1%',
    images: [
      unsplash('photo-1553413077-190dd305871c'),
      GALLERY_POOL[1]
    ],
    desc: 'RAW SCRAPED: Operational industrial shed with connected power and borewell. Direct sale by secured creditor under SARFAESI Security Interest Rules.'
  }
];

// Computed properties with end timestamps and formatted fields
export const INITIAL_PROPERTIES = [
  ...RAW_PROPERTIES.map((p) => {
    const auctionEnd = Date.now() + p.daysAhead * 24 * 60 * 60 * 1000;
    const emd = Math.round((p.reserve * (p.emdPct || 10)) / 100);
    return {
      ...p,
      auctionEnd,
      emd,
      verified: true,
      status: 'PUBLISHED',
      verifiedDate: 'Nov 12, 2026',
    };
  }),
  ...UNVERIFIED_SCRAPED_PROPERTIES.map((p) => {
    const auctionEnd = Date.now() + p.daysAhead * 24 * 60 * 60 * 1000;
    const emd = Math.round((p.reserve * (p.emdPct || 10)) / 100);
    return {
      ...p,
      auctionEnd,
      emd,
    };
  })
];

// Format Price in Indian system: ₹78.00 Lakhs / ₹1.45 Cr
export function formatPrice(n) {
  if (n == null || isNaN(n)) return '—';
  if (n >= 10000000) {
    const val = (n / 10000000).toFixed(2);
    return `₹ ${val} Crores`;
  }
  const val = (n / 100000).toFixed(2);
  return `₹ ${val} Lakhs`;
}

// Compact price for cards: ₹78.00 Lakhs / ₹1.45 Cr
export function formatPriceShort(n) {
  if (n == null || isNaN(n)) return '—';
  if (n >= 10000000) {
    const val = (n / 10000000).toFixed(2);
    return `₹ ${val} Cr`;
  }
  const val = (n / 100000).toFixed(2);
  return `₹ ${val} Lakhs`;
}

export function formatRupees(n) {
  if (n == null || isNaN(n)) return '—';
  return '₹ ' + Number(n).toLocaleString('en-IN');
}

export function formatSqft(n) {
  return n ? Number(n).toLocaleString('en-IN') + ' sq.ft' : '—';
}

export function typeLabel(t) {
  const map = {
    residential: 'Residential',
    commercial: 'Commercial',
    land: 'Land / Plot',
    industrial: 'Industrial',
  };
  return map[t] || t;
}

// Calculate remaining time object
export function timeRemaining(endTs) {
  let total = endTs - Date.now();
  if (total < 0) total = 0;
  const d = Math.floor(total / 86400000);
  const h = Math.floor((total % 86400000) / 3600000);
  const m = Math.floor((total % 3600000) / 60000);
  const s = Math.floor((total % 60000) / 1000);
  return { d, h, m, s, total };
}

export function pad2(n) {
  return String(n).padStart(2, '0');
}
