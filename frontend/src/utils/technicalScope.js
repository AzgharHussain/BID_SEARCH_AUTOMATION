// Dynamic technical scope generator for tenders/projects
// Follows strict 2-sentence structure:
// Sentence 1: The assignment encompasses {act1}, {act2}, and {act3}.
// Sentence 2: Key technical requirements involve {req1}, {req2}, quality assurance, and {req3}.
// Guaranteed zero client information, tender numbers, budgets, deadlines, or locations.

const SCOPE_PATTERNS = [
  // 1. CCTV, Smart Surveillance & Security Control Rooms
  {
    regex: /\b(cctv|surveillance|cameras?|security systems?|control rooms?|command cent(?:er|re)|vms|video management|access control)\b/i,
    sentence1: 'The assignment encompasses comprehensive field deployment of high-definition CCTV surveillance infrastructure, network video recording integration with multi-point sensor arrays, and the operationalization of a centralized digital security control room.',
    sentence2: 'Key technical requirements involve High-Definition Video Surveillance Systems, Network Video Recording & allied IT Infrastructure, quality assurance, and integration with centralized real-time security monitoring systems.',
    phrase: 'smart surveillance and security project',
    title: 'Smart Surveillance & Security Project'
  },
  // 2. Roads, Highways, Corridors & Pavements
  {
    regex: /\b(highways?|roads?|corridors?|pavements?|bridges?|flyovers?|expressways?|culverts?|carriageways?|traffic engineering|traffic management|toll plaza|ser-\d+)\b/i,
    sentence1: 'The assignment encompasses comprehensive road asset inventory acquisition, high-precision corridor condition surveys, and the deployment of an enterprise digital transportation infrastructure database.',
    sentence2: 'Key technical requirements involve Road Asset Management Systems, Pavement Condition & Corridor Spatial Engineering, quality assurance, and integration with public transportation monitoring systems.',
    phrase: 'transport and infrastructure project',
    title: 'Transport & Infrastructure Project'
  },
  // 3. Railways & Mass Rapid Transit
  {
    regex: /\b(railways?|rapid transit|metro rail|rail tracks?|rolling stocks?|freight corridor)\b/i,
    sentence1: 'The assignment encompasses railway alignment data acquisition, high-precision permanent way and asset surveys, and the deployment of a centralized digital railway infrastructure database.',
    sentence2: 'Key technical requirements involve Transit Corridor Spatial Analytics, Railway Track & Asset Engineering, quality assurance, and integration with operational train monitoring systems.',
    phrase: 'railway and mass transit project',
    title: 'Railway & Mass Transit Project'
  },
  // 4. Drone, LiDAR, Cadastral & Core WebGIS
  {
    regex: /\b(drones?|uavs?|lidar|dgps|cadastral|photogrammetry|gis mapping|geospatial|remote sensing|topographic surveys?|cartograph\w*|webgis)\b/i,
    sentence1: 'The assignment encompasses comprehensive field data acquisition, high-precision geospatial surveys, and the deployment of an enterprise WebGIS digital database.',
    sentence2: 'Key technical requirements involve Enterprise GIS Solutions, Digital Surveying & Geodatabase Engineering, quality assurance, and integration with public infrastructure monitoring systems.',
    phrase: 'geospatial and digital survey project',
    title: 'Geospatial & Digital Survey Project'
  },
  // 5. Electro-Mechanical, Facility Maintenance & ARMO/RMO
  {
    regex: /\b(armo|rmo|e\s*&\s*m|e and m|electro-mechanical|firefighting|cooling towers?|dg sets?|hvac|air conditioning|plumbing|sanitary works?|repair of existing|maintenance of existing)\b/i,
    sentence1: 'The assignment encompasses electro-mechanical facility assessment, infrastructure asset inventorying, and the deployment of an enterprise facility operations digital database.',
    sentence2: 'Key technical requirements involve Electro-Mechanical Systems Engineering, Facility Maintenance & Asset Registry Management, quality assurance, and integration with facility operations monitoring systems.',
    phrase: 'facility operations and infrastructure project',
    title: 'Facility Operations & Infrastructure Project'
  },
  // 6. Water Resources, Irrigation, Dams & Hydrology
  {
    regex: /\b(water resources?|iwrm|irrigat\w*|hydrolog\w*|drainage|flood\w*|\bdams?\b|canals?|river basins?|water supply|watersheds?|aquifers?|reservoirs?|wastewater|sewerage|water balance|water security|hydrogeolog\w*)\b/i,
    sentence1: 'The assignment encompasses comprehensive hydrological data acquisition, water distribution asset mapping and catchment surveys, and the deployment of an enterprise water resource management digital database.',
    sentence2: 'Key technical requirements involve Hydrological Modeling & Water Network Engineering, Spatial Asset Inventory & Geodatabase Solutions, quality assurance, and integration with public water infrastructure monitoring systems.',
    phrase: 'water resources project',
    title: 'Water Resources Project'
  },
  // 7. Energy, Power, Solar & SCADA
  {
    regex: /\b(solar|power sector|power grid|power plant|photovoltaic|substations?|\bgrids?\b|electricity|decarbonization|transmissions?|scada|transformers?|electrical works?|electrification)\b/i,
    sentence1: 'The assignment encompasses power network asset characterization, renewable energy site mapping and electrical equipment evaluation, and the deployment of an enterprise digital power distribution database.',
    sentence2: 'Key technical requirements involve Power Transmission & Distribution Asset Engineering, Solar PV & SCADA System Integration, quality assurance, and integration with public utility monitoring systems.',
    phrase: 'energy and power sector project',
    title: 'Energy & Power Sector Project'
  },
  // 8. Environment, Climate Resilience & Bio-Medical Waste
  {
    regex: /\b(environments?|forest\w*|climates?|waste management|bio-medical|pollution|ecolog\w*|biodiversity|rehabilitation|conservation|subsidence|effluents?|sanitation|garbage)\b/i,
    sentence1: 'The assignment encompasses comprehensive baseline environmental data collection, ecological habitat and emissions mapping, and the deployment of an enterprise digital environmental database.',
    sentence2: 'Key technical requirements involve Environmental Impact Assessment Solutions, Ecological Monitoring & Geodatabase Engineering, quality assurance, and integration with statutory environmental compliance systems.',
    phrase: 'environment and climate resilience project',
    title: 'Environment & Climate Resilience Project'
  },
  // 9. Agriculture & Rural Development
  {
    regex: /\b(agricultur\w*|farmlands?|\bcrops?\b|agroforestry|rural livelihoods?|smallholders?|farming|horticultur\w*|livestock|veterinary|\bsoils?\b)\b/i,
    sentence1: 'The assignment encompasses agricultural land parcel data acquisition, high-resolution crop health and vegetation surveys, and the deployment of an enterprise digital agricultural database.',
    sentence2: 'Key technical requirements involve Agri-Spatial Analytics & Remote Sensing, Land Capability & Crop Health Assessment, quality assurance, and integration with agricultural decision support systems.',
    phrase: 'agriculture and rural development project',
    title: 'Agriculture & Rural Development Project'
  },
  // 10. Healthcare & Biomedical Systems
  {
    regex: /\b(healthcare|hospitals?|medical|clinical|epidemiolog\w*|patients?|telemedicine|dispensar\w*)\b/i,
    sentence1: 'The assignment encompasses comprehensive healthcare facility inventorying, spatial health infrastructure assessments, and the deployment of a centralized healthcare digital database.',
    sentence2: 'Key technical requirements involve Public Health Analytics Solutions, Clinical Asset & Health Informatics Engineering, quality assurance, and integration with public healthcare monitoring systems.',
    phrase: 'healthcare systems project',
    title: 'Healthcare Systems Project'
  },
  // 11. Software, IT Solutions, Cloud & MIS
  {
    regex: /\b(softwares?|information systems?|\bmis\b|web portals?|web applications?|cloud computing|data cent(?:er|re)|application development|databases?|\bict\b|digitization|digital twins?)\b/i,
    sentence1: 'The assignment encompasses enterprise systems requirement analysis, secure cloud-native application engineering, and the deployment of a scalable enterprise digital database.',
    sentence2: 'Key technical requirements involve Enterprise Software Architecture Solutions, Relational Database Engineering & Cloud Integration, quality assurance, and integration with automated operational monitoring systems.',
    phrase: 'software and IT solutions project',
    title: 'Software & IT Solutions Project'
  },
  // 12. Urban Infrastructure, Municipal Planning & Construction
  {
    regex: /\b(urban planning|municip\w*|town planning|\bcities\b|\bcity\b|housing|smart city|civic infrastructure|slums?|\bwards?\b|property tax|construction|civil works?|buildings?|structures?|toilet blocks?)\b/i,
    sentence1: 'The assignment encompasses comprehensive municipal asset mapping, high-precision urban infrastructure surveys, and the deployment of an enterprise civic digital database.',
    sentence2: 'Key technical requirements involve Urban Spatial Planning Solutions, Municipal Cadastre & Infrastructure Engineering, quality assurance, and integration with municipal governance monitoring systems.',
    phrase: 'urban infrastructure project',
    title: 'Urban Infrastructure Project'
  },
  // 13. Telecommunications & Fiber Networks
  {
    regex: /\b(telecom\w*|optical fibers?|\bofc\b|fiber optic|broadband|wireless networks?|telephony)\b/i,
    sentence1: 'The assignment encompasses telecommunication corridor data acquisition, optical fiber route surveys, and the deployment of an enterprise network GIS database.',
    sentence2: 'Key technical requirements involve Telecommunication Network Engineering, Fiber Asset Inventory & Spatial Management, quality assurance, and integration with telecommunication operations monitoring systems.',
    phrase: 'telecommunication infrastructure project',
    title: 'Telecommunication Infrastructure Project'
  },
  // 14. Mining & Geological Resources
  {
    regex: /\b(mining|minerals?|geology|geological|quarr\w*)\b/i,
    sentence1: 'The assignment encompasses mineral terrain data acquisition, high-precision geological mapping surveys, and the deployment of an enterprise geological spatial database.',
    sentence2: 'Key technical requirements involve Geological Spatial Modeling Solutions, Mineral Asset & Terrain Engineering, quality assurance, and integration with statutory mining compliance monitoring systems.',
    phrase: 'mining and geological resources project',
    title: 'Mining & Geological Resources Project'
  },
  // 15. Ports, Maritime & Coastal
  {
    regex: /\b(ports?|maritime|harbors?|harbours?|jetties|jetty|inland waterways?|bathymetr\w*)\b/i,
    sentence1: 'The assignment encompasses bathymetric field data acquisition, coastal and maritime corridor surveys, and the deployment of an enterprise maritime spatial database.',
    sentence2: 'Key technical requirements involve Hydrographic & Coastal Asset Engineering, Marine Geodatabase Solutions, quality assurance, and integration with vessel traffic and port monitoring systems.',
    phrase: 'maritime and port infrastructure project',
    title: 'Maritime & Port Infrastructure Project'
  },
  // 16. Financial, Audit & Governance Advisory
  {
    regex: /\b(financ\w*|audits?|governance|\btax\b|taxes|accounting|advisory services?|macro economic|trade finance)\b/i,
    sentence1: 'The assignment encompasses institutional data collection, systematic financial and operational process reviews, and the deployment of an enterprise governance tracking database.',
    sentence2: 'Key technical requirements involve Financial Governance Advisory Solutions, Operational Process & Systems Engineering, quality assurance, and integration with statutory governance monitoring systems.',
    phrase: 'financial and governance advisory project',
    title: 'Financial & Governance Advisory Project'
  }
];

export function cleanProjectTitle(rawTitle) {
  if (!rawTitle) return 'Technology & Geospatial Infrastructure Project';
  let t = String(rawTitle).trim();
  if (t.startsWith('[') && t.endsWith(']')) {
    t = t.slice(1, -1).trim();
  }
  t = t.replace(/^(LOAN|GRANT|TA|IFB|RFP|NIT|Tender\s*No\.?)\s*[-#A-Za-z0-9/]+(\s+[A-Za-z]{3})?:\s*/i, '');
  t = t.replace(/^Estimate\s+No\.?\s*[-#A-Za-z0-9/\s]+:\s*/i, '');
  const subHeadMatch = t.match(/(?:Sub\s*Head|SH[:\s-]+)\s*(.+)/i);
  if (subHeadMatch && subHeadMatch[1]) {
    t = subHeadMatch[1].trim();
  }
  t = t.replace(/\s*\((?:Tender\s*ID|Ref(?:erence)?\s*No\.?|Package\s*No\.?|Notice\s*No\.?)\s*:[^)]*\)/i, '');
  t = t.replace(/\s*\([A-Za-z0-9_-]+\)\s*$/, '');
  t = t.replace(/^['"]+|['"]+$/g, '').trim();
  return t || 'Technology & Geospatial Infrastructure Project';
}

export function getProjectTechnicalScope(tender) {
  const rawTitle = tender?.title || tender?.project_name || '';
  const cleanTitle = cleanProjectTitle(rawTitle);

  if (!tender) {
    return {
      cleanTitle,
      scopeParagraph: 'The assignment encompasses comprehensive field data acquisition, digital technical surveys, and the deployment of an enterprise digital spatial database. Key technical requirements involve Enterprise Technology Solutions, Digital Engineering & Geodatabase Architecture, quality assurance, and integration with public infrastructure monitoring systems.',
      sectorPhrase: 'technology and infrastructure project',
      sectorTitle: 'Technology & Infrastructure Project'
    };
  }

  const combined = [
    rawTitle,
    tender.project_sector || '',
    tender.scope_of_work || '',
    tender.description || '',
    tender.department || '',
    tender.category || '',
    Array.isArray(tender.keywords) ? tender.keywords.join(' ') : (tender.keywords || '')
  ].join(' ').toLowerCase();

  for (const item of SCOPE_PATTERNS) {
    if (item.regex.test(combined)) {
      return {
        cleanTitle,
        scopeParagraph: `${item.sentence1} ${item.sentence2}`,
        sectorPhrase: item.phrase,
        sectorTitle: item.title
      };
    }
  }

  return {
    cleanTitle,
    scopeParagraph: 'The assignment encompasses comprehensive field data acquisition, digital technical surveys, and the deployment of an enterprise digital spatial database. Key technical requirements involve Enterprise Technology Solutions, Digital Engineering & Geodatabase Architecture, quality assurance, and integration with public infrastructure monitoring systems.',
    sectorPhrase: 'technology and infrastructure project',
    sectorTitle: 'Technology & Infrastructure Project'
  };
}
