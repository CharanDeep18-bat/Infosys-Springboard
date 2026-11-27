// Financial Knowledge Base & Vector Index Data Store for Module 3
import { SEED_COMPANIES, SAMPLE_CHUNKS } from "./seedData";
import { getStoredDocuments } from "./documentData";

export const INDEXING_STATUSES = [
  "Ready",
  "Indexed",
  "Queued",
  "Processing",
  "Uploaded",
  "Cancelled",
  "Error"
];
export const WORKFLOW_STAGES = [
  {
    step: 1,
    id: "received",
    title: "Document received",
    description: "PDF file ingested, binary payload verified, SHA-256 cryptographic checksum calculated."
  },
  {
    step: 2,
    id: "extracted",
    title: "Text extracted",
    description: "Optical Character Recognition (OCR) applied to extract clean text streams, coordinate table layouts, and footnotes."
  },
  {
    step: 3,
    id: "chunked",
    title: "Document split into chunks",
    description: "Recursive semantic token chunking splits filing into contextual blocks (512 tokens / 64 token overlap)."
  },
  {
    step: 4,
    id: "embedded",
    title: "Embeddings generated",
    description: "1536-dimensional dense vector embeddings generated via OpenAI text-embedding-3-small."
  },
  {
    step: 5,
    id: "indexed",
    title: "Vectors indexed",
    description: "Embeddings structured into Hierarchical Navigable Small World (HNSW) vector index graph with cosine distance."
  },
  {
    step: 6,
    id: "ready",
    title: "Document ready for retrieval",
    description: "Citation grounding verified; filing active for semantic search and multi-agent reasoning synthesis."
  }
];
export const INITIAL_INDEXING_RECORDS = [];
export const MOCK_RETRIEVAL_PASSAGES = [
  {
    id: "ret-1",
    queryKeywords: ["margin", "ebit", "operating margin", "variance", "infosys", "tcs"],
    docName: "Infosys-Annual-Report-2023-24.pdf",
    company: "Infosys Limited",
    ticker: "INFY",
    page: 112,
    section: "Consolidated Statement of Profit and Loss",
    relevanceScore: 0.942,
    relevanceTier: "High Match (94.2%)",
    tokens: 432,
    content: "Revenue from operations for the year ended March 31, 2024 stood at ₹153,670 crore, compared to ₹146,767 crore in the previous year, registering a growth of 4.7% (1.4% in constant currency terms). Operating profit was ₹31,861 crore as against ₹30,905 crore in the prior year, yielding an operating margin of 20.7% compared to 21.0% in FY23. Net profit attributable to owners was ₹26,233 crore, reflecting growth of 8.9%."
  },
  {
    id: "ret-2",
    queryKeywords: ["margin", "ebit", "tcs", "operating margin", "variance", "infosys"],
    docName: "TCS-Annual-Report-2023-24.pdf",
    company: "Tata Consultancy Services",
    ticker: "TCS",
    page: 94,
    section: "Consolidated Statement of Profit and Loss",
    relevanceScore: 0.938,
    relevanceTier: "High Match (93.8%)",
    tokens: 412,
    content: "Consolidated revenue from operations increased to ₹240,893 crore ($29.08B), representing an expansion of 6.8% YoY (3.4% in constant currency terms). Operating margin for the full year reached 24.6%, expanding 50 basis points over the prior fiscal year, supported by productivity gains and pyramid optimization. Profit after tax reached ₹46,585 crore, up 10.5% YoY, representing a net margin of 19.3%."
  },
  {
    id: "ret-3",
    queryKeywords: ["deal", "tcv", "order book", "signings", "contract"],
    docName: "TCS-Annual-Report-2023-24.pdf",
    company: "Tata Consultancy Services",
    ticker: "TCS",
    page: 45,
    section: "Management Discussion - Order Book TCV",
    relevanceScore: 0.912,
    relevanceTier: "High Match (91.2%)",
    tokens: 384,
    content: "Record annual order book Total Contract Value (TCV) closed at an all-time high of $42.7 billion with broad-based wins across North America, the UK, and continental European transformation accounts. Q4 TCV alone reached $13.2 billion."
  },
  {
    id: "ret-4",
    queryKeywords: ["deal", "tcv", "infosys", "large deal", "pipeline"],
    docName: "Infosys-Annual-Report-2023-24.pdf",
    company: "Infosys Limited",
    ticker: "INFY",
    page: 87,
    section: "Segment Performance & Deal Velocity",
    relevanceScore: 0.904,
    relevanceTier: "High Match (90.4%)",
    tokens: 396,
    content: "Total contract value (TCV) of large deal signings reached an all-time record of $17.7 billion in FY24, with net new deals constituting 52% of total signings, underscoring enduring client trust in our Cobalt and Topaz generative AI platforms."
  },
  {
    id: "ret-5",
    queryKeywords: ["tax", "red flag", "apple", "state aid", "cjeu", "ireland", "fine"],
    docName: "Apple-10K-FY2024.pdf",
    company: "Apple Inc.",
    ticker: "AAPL",
    page: 61,
    section: "Note 5 - Income Taxes",
    relevanceScore: 0.951,
    relevanceTier: "High Match (95.1%)",
    tokens: 420,
    content: "During the fourth quarter of 2024, the Company recorded a one-time income tax charge of $10.2 billion associated with the CJEU judgment in the European State Aid case. This non-operating tax expense increased the effective tax rate for FY24 to 24.1% compared to 14.7% in FY23."
  },
  {
    id: "ret-6",
    queryKeywords: ["china", "greater china", "apple", "revenue decline", "hardware"],
    docName: "Apple-10K-FY2024.pdf",
    company: "Apple Inc.",
    ticker: "AAPL",
    page: 34,
    section: "Item 7 - Segment Net Sales by Geographic Region",
    relevanceScore: 0.923,
    relevanceTier: "High Match (92.3%)",
    tokens: 410,
    content: "Greater China net sales decreased 8% during 2024 compared to 2023, falling from $72.56 billion to $66.95 billion, primarily due to lower net sales of iPhone and foreign currency headwinds against the U.S. dollar."
  },
  {
    id: "ret-7",
    queryKeywords: ["capex", "capital expenditures", "microsoft", "azure", "cloud", "ai", "gpu"],
    docName: "Microsoft-10K-FY2024.pdf",
    company: "Microsoft Corporation",
    ticker: "MSFT",
    page: 43,
    section: "Liquidity and Capital Resources - CapEx",
    relevanceScore: 0.935,
    relevanceTier: "High Match (93.5%)",
    tokens: 440,
    content: "Capital expenditures including assets acquired under finance leases were $55.7 billion, compared to $31.9 billion in FY 2023. Cash paid for property and equipment was $44.5 billion. These investments are driven by cloud and AI demand, primarily for data centers, compute infrastructure, and networking hardware required to train and serve frontier generative AI models across our commercial cloud."
  },
  {
    id: "ret-8",
    queryKeywords: ["intelligent cloud", "azure", "microsoft", "copilot", "cloud revenue"],
    docName: "Microsoft-10K-FY2024.pdf",
    company: "Microsoft Corporation",
    ticker: "MSFT",
    page: 40,
    section: "Item 7 - Segment Results of Operations",
    relevanceScore: 0.928,
    relevanceTier: "High Match (92.8%)",
    tokens: 415,
    content: "Intelligent Cloud revenue increased $17.4 billion or 20% to $105.4 billion, driven by Azure and other cloud services growth of 30%. Azure growth included approximately 800 basis points of contribution from artificial intelligence services."
  },
  {
    id: "ret-9",
    queryKeywords: ["subcontractor", "pyramid", "employee cost", "margin drag", "offshore"],
    docName: "Infosys-Annual-Report-2023-24.pdf",
    company: "Infosys Limited",
    ticker: "INFY",
    page: 129,
    section: "Note 21 - Operating Expenses",
    relevanceScore: 0.887,
    relevanceTier: "Strong Match (88.7%)",
    tokens: 360,
    content: "Technical sub-contractor expenses for the year ended March 31, 2024 were ₹14,562 Cr (9.5% of revenue) versus ₹15,920 Cr (10.8% of revenue). Subcontractor outlays continued to be disciplined through internal project rotation and offshore delivery substitution."
  },
  {
    id: "ret-10",
    queryKeywords: ["subcontractor", "tcs", "employee benefit", "cost structure"],
    docName: "TCS-Audited-Financial-Statements-FY24.pdf",
    company: "Tata Consultancy Services",
    ticker: "TCS",
    page: 8,
    section: "Consolidated Statement of Profit and Loss - Schedule",
    relevanceScore: 0.882,
    relevanceTier: "Strong Match (88.2%)",
    tokens: 375,
    content: "Employee benefit expenses stood at ₹133,456 crore (55.4% of total revenue) compared to ₹127,522 crore in FY23. Fees to external consultants and sub-contractors accounted for 8.0% of revenue, demonstrating superior in-house pyramid utilization."
  }
];

export const SAMPLE_QUERIES = [
  "Compare operating margin and deal TCV for Infosys and TCS in FY24",
  "What financial red flags or tax charges were disclosed in Apple's FY24 Form 10-K?",
  "Analyze Microsoft's $55.7B CapEx spending and Azure AI monetization",
  "Technical subcontractor expenses and pyramid margin drag",
  "Greater China market revenue contraction and foreign currency headwinds"
];

const KB_STORAGE_KEY = "finresearch_kb_records_v3";

export function getStoredIndexingRecords() {
  return [];
}

export function saveStoredIndexingRecords(records) {
}