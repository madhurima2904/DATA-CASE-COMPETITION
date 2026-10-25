// Duplicate-matching logic (JavaScript port of request_form/mdm.py).
// Name similarity 0-100, robust to abbreviations, word order, spacing and branch numbers.

const ABBREVIATIONS = {
  natl: "national", univ: "university", hosp: "hospital", intl: "international",
  gen: "general", med: "medical", ctr: "centre", center: "centre", inst: "institute",
  lab: "laboratory", labs: "laboratory", diag: "diagnostic", clinc: "clinic",
  sg: "singapore", kl: "kuala lumpur", hcmc: "ho chi minh city", bkk: "bangkok",
};
const STOPWORDS = new Set(["pte", "ltd", "limited", "inc", "co", "the", "sdn", "bhd", "pt", "tbk"]);

function normalise(name) {
  const tokens = String(name || "").toLowerCase().replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter(Boolean);
  const out = [];
  for (let t of tokens) {
    t = ABBREVIATIONS[t] || t;
    if (/^\d+$/.test(t)) t = String(parseInt(t, 10));
    for (const part of t.split(" ")) if (!STOPWORDS.has(part)) out.push(part);
  }
  return out.join(" ");
}

// Indel-normalised similarity, same definition as rapidfuzz.fuzz.ratio
function ratio(a, b) {
  if (!a.length && !b.length) return 100;
  const m = a.length, n = b.length;
  let prev = new Array(n + 1).fill(0);
  for (let i = 1; i <= m; i++) {
    const cur = new Array(n + 1).fill(0);
    for (let j = 1; j <= n; j++) {
      cur[j] = a[i - 1] === b[j - 1] ? prev[j - 1] + 1 : Math.max(prev[j], cur[j - 1]);
    }
    prev = cur;
  }
  return (200 * prev[n]) / (m + n);
}

function tokenSortRatio(a, b) {
  return ratio(a.split(" ").sort().join(" "), b.split(" ").sort().join(" "));
}

function tokenSetRatio(a, b) {
  const sa = new Set(a.split(" ")), sb = new Set(b.split(" "));
  const inter = [...sa].filter((t) => sb.has(t)).sort();
  const diffAB = [...sa].filter((t) => !sb.has(t)).sort();
  const diffBA = [...sb].filter((t) => !sa.has(t)).sort();
  if (inter.length && (!diffAB.length || !diffBA.length)) return 100;
  const sect = inter.join(" ");
  const t1 = [sect, diffAB.join(" ")].filter(Boolean).join(" ");
  const t2 = [sect, diffBA.join(" ")].filter(Boolean).join(" ");
  return Math.max(sect ? ratio(sect, t1) : 0, sect ? ratio(sect, t2) : 0, ratio(t1, t2));
}

function similarity(x, y) {
  const a = normalise(x), b = normalise(y);
  if (!a || !b) return 0;
  const mixed = (tokenSetRatio(a, b) + tokenSortRatio(a, b)) / 2;
  let score = Math.max(mixed, ratio(a.replace(/ /g, ""), b.replace(/ /g, "")));
  const na = new Set(a.split(" ").filter((t) => /^\d+$/.test(t)));
  const nb = new Set(b.split(" ").filter((t) => /^\d+$/.test(t)));
  const same = na.size === nb.size && [...na].every((t) => nb.has(t));
  if (na.size && nb.size && !same) score *= 0.7;
  return score;
}

// records: [{code, name, entity, country, reg_no}]
function findDuplicates(records, name, regNo, country, limit = 5) {
  if (!String(name || "").trim() && !String(regNo || "").trim()) return [];
  const out = records.map((r) => {
    let s = similarity(name, r.name), reason = "Similar name";
    if (country && r.country && r.country !== country) s *= 0.8;
    if (regNo && r.reg_no && r.reg_no.trim().toUpperCase() === String(regNo).trim().toUpperCase()) {
      s = 100; reason = "Same registration no.";
    }
    return { ...r, score: Math.round(s), reason };
  });
  return out.filter((r) => r.score >= 75).sort((a, b) => b.score - a.score).slice(0, limit);
}

function duplicateLevel(score) {
  return score >= 90 ? "block" : score >= 80 ? "warn" : "ok";
}

if (typeof module !== "undefined") module.exports = { normalise, similarity, findDuplicates, duplicateLevel };
