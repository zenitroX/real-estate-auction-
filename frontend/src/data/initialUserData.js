export const INITIAL_USER = {
  name: 'Udhaya Kumar R',
  email: 'udhaya.kumar@skandx.demo',
  phone: '+91 98407 22110',
  city: 'Chennai',
  pan: 'ABZPU1234K',
  aadhaar: 'XXXX XXXX 4417',
  memberSince: 'Jan 2024',
  initials: 'UK',
  isVerified: true,
  isLoggedIn: true,
};

// Seeded bids matching screenshot:
export const INITIAL_WISHLIST = ['p1', 'p2', 'p3', 'p4', 'p5'];

export const INITIAL_NOTIFICATIONS = [
  {
    id: 'n1',
    type: 'bid',
    title: 'Bid placed successfully',
    text: 'Your bid of ₹80.50 Lakhs is currently the leading bid on Independent House (3 BHK).',
    time: '45 mins ago',
    unread: true,
  },
  {
    id: 'n2',
    type: 'ending',
    title: 'Auction ending soon',
    text: 'Luxury Villa (4 BHK) auction closes in less than 3 days. Prepare your final bid.',
    time: '2 hours ago',
    unread: true,
  },
  {
    id: 'n3',
    type: 'kyc',
    title: 'KYC Document Status',
    text: 'Please upload cancelled cheque or bank statement proof to unlock bidding on ₹1 Cr+ assets.',
    time: 'Yesterday',
    unread: true,
  },
  {
    id: 'n4',
    type: 'win',
    title: 'Auction Won!',
    text: 'Congratulations! Your winning bid for Commercial Showroom, Banjara Hills has been approved by the asset committee.',
    time: '3 days ago',
    unread: false,
  },
  {
    id: 'n5',
    type: 'bank',
    title: 'New SBI Auction Catalog',
    text: 'SBI has listed 12 new SARFAESI e-auction properties across Chennai & Bengaluru metro areas.',
    time: '4 days ago',
    unread: false,
  },
];

export const INITIAL_KYC = [
  { id: 'pan', name: 'PAN Card', identifier: 'ABZPU1234K', status: 'Verified', date: 'Jan 15, 2024' },
  { id: 'aadhaar', name: 'Aadhaar Card', identifier: 'XXXX XXXX 4417', status: 'Verified', date: 'Jan 16, 2024' },
  { id: 'bank', name: 'Bank Account Proof', identifier: 'Cancelled Cheque · HDFC Bank', status: 'Pending', date: 'Action Needed' },
];

export const INITIAL_LEADS = [
  {
    id: 'lead-1',
    customerName: 'Karthik Narayanan',
    phone: '+91 98401 22345',
    email: 'karthik.n@gmail.com',
    propertyId: 'p1',
    propertyTitle: 'Independent House (3 BHK)',
    locality: 'Madipakkam, Chennai',
    inquiryType: 'Site Visit Inspection',
    message: 'Interested in physical inspection of the independent house this Saturday. Please confirm bank officer availability.',
    time: '25 mins ago',
    status: 'NEW'
  },
  {
    id: 'lead-2',
    customerName: 'Anandhi Srinivasan',
    phone: '+91 97909 88712',
    email: 'anandhi.s@outlook.com',
    propertyId: 'p2',
    propertyTitle: 'Luxury Villa (4 BHK)',
    locality: 'OMR, Chennai',
    inquiryType: 'Legal Search Report',
    message: 'Need 30-year encumbrance certificate and SARFAESI possession notice copy before depositing EMD.',
    time: '2 hours ago',
    status: 'IN_REVIEW'
  },
  {
    id: 'lead-3',
    customerName: 'Suresh Menon',
    phone: '+91 94440 55123',
    email: 'suresh.menon@venturecapital.in',
    propertyId: 'p5',
    propertyTitle: 'Commercial Building (T. Nagar)',
    locality: 'T. Nagar, Chennai',
    inquiryType: 'EMD & Financing Guidance',
    message: 'Evaluating this commercial building for IT firm office. Want bridge loan assistance for EMD.',
    time: 'Yesterday',
    status: 'CONTACTED'
  }
];

export const FAQS = [
  {
    q: 'How do I place my first bid on SKANDX?',
    a: 'Browse to any live property, review the bank inspection notice, verify your KYC, deposit the 10% Earnest Money Deposit (EMD), and click "Place Bid Now". Our dedicated auction desk will provide live assistance during your first auction.',
  },
  {
    q: 'When is the EMD refunded if I do not win?',
    a: 'If your bid is not the winning bid, the full EMD amount is securely refunded directly to your original source bank account within 3 to 7 working days following auction closure.',
  },
  {
    q: 'Are these properties physically verified and legally vetted?',
    a: 'Yes. Every listed bank property undergoes comprehensive title search (30-year search report), encumbrance certificate (EC) scrutiny, and on-site physical inspection by our empanelled legal counsel.',
  },
  {
    q: 'Can I visit and inspect the property before bidding?',
    a: 'Absolutely. Use the "Site View / Visit" button on any property page. Our field relationship officer will arrange an accompanied physical inspection with the bank recovery officer.',
  },
  {
    q: 'Can I avail bank loan or financing for auction properties?',
    a: 'Yes. We partner with leading financial institutions and NBFCs offering pre-approved auction bridge loans and home loans up to 75% of the property value post-auction victory.',
  },
];
