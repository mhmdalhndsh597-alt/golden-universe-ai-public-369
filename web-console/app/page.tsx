"use client";

import { useEffect, useState } from "react";

type Locale = "en" | "ar";

type NodeRow = {
  id: string;
  region: string;
  gpu: string;
  tflops: number;
  status: "healthy" | "degraded";
};

const nodes: NodeRow[] = [
  { id: "GPU-EU-01", region: "Frankfurt", gpu: "H200 SXM", tflops: 1.86, status: "healthy" },
  { id: "GPU-US-03", region: "Virginia", gpu: "H100 NVL", tflops: 1.31, status: "healthy" },
  { id: "GPU-AE-02", region: "Dubai", gpu: "A100 80GB", tflops: 0.62, status: "healthy" },
  { id: "GPU-SG-01", region: "Singapore", gpu: "H100 PCIe", tflops: 0.51, status: "degraded" },
];

const copy = {
  en: {
    title: "Neural Grid",
    subtitle: "Global Distributed GPU Compute",
    peta: "Network PetaFLOPS",
    active: "Active GPU Nodes",
    latency: "API P50 Latency",
    availability: "Grid Availability",
    nodeTable: "Active GPU Nodes",
    license: "Enterprise License",
    activate: "Activate",
    licenseKey: "Enterprise license token",
  },
  ar: {
    title: "شبكة الذكاء",
    subtitle: "حوسبة GPU موزعة عالمياً",
    peta: "بيتا فلوب للشبكة",
    active: "عقد GPU النشطة",
    latency: "زمن الاستجابة P50",
    availability: "توفر الشبكة",
    nodeTable: "عقد GPU النشطة",
    license: "ترخيص المؤسسة",
    activate: "تفعيل",
    licenseKey: "رمز ترخيص المؤسسة",
  },
} as const;

export default function Page() {
  const [locale, setLocale] = useState<Locale>("en");
  const [basePeta, setBasePeta] = useState(4.87);
  const [license, setLicense] = useState("");
  const [licenseStatus, setLicenseStatus] = useState("");
  const text = copy[locale];

  useEffect(() => {
    const timer = window.setInterval(() => {
      setBasePeta((current) => Math.max(4.8, current + (Math.random() - 0.5) * 0.025));
    }, 1800);
    return () => window.clearInterval(timer);
  }, []);

  function activateLicense(): void {
    setLicenseStatus(
      license.trim()
        ? "License format accepted. Signature verification is performed by the enterprise control plane."
        : "Enter a signed enterprise license token.",
    );
  }

  return (
    <main
      dir={locale === "ar" ? "rtl" : "ltr"}
      style={{
        minHeight: "100vh",
        background: "#090909",
        color: "#f4ead0",
        fontFamily: "Inter, system-ui, sans-serif",
        padding: "32px",
      }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
        <div>
          <div style={{ color: "#d4af37", letterSpacing: "0.16em", fontSize: 12, fontWeight: 700 }}>
            GOLDEN UNIVERSE AI CENTER
          </div>
          <h1 style={{ margin: "6px 0 2px", fontSize: 34 }}>{text.title}</h1>
          <p style={{ margin: 0, color: "#9d9279" }}>{text.subtitle}</p>
        </div>
        <button
          type="button"
          onClick={() => setLocale(locale === "en" ? "ar" : "en")}
          style={{ border: "1px solid #d4af37", background: "#17130b", color: "#d4af37", borderRadius: 8, padding: "10px 14px" }}
        >
          {locale === "en" ? "العربية" : "English"}
        </button>
      </header>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 14, marginBottom: 18 }}>
        {[
          [text.peta, `${basePeta.toFixed(2)} PF`, "#d4af37"],
          [text.active, "128", "#7ee7a5"],
          [text.latency, "42 ms", "#79bfff"],
          [text.availability, "99.99%", "#d4af37"],
        ].map(([label, value, accent]) => (
          <article key={label} style={{ background: "#111", border: "1px solid #29251d", borderRadius: 12, padding: 18 }}>
            <div style={{ color: "#a79a7e", fontSize: 12 }}>{label}</div>
            <strong style={{ color: accent, display: "block", fontSize: 25, marginTop: 8 }}>{value}</strong>
          </article>
        ))}
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 18 }}>
        <article style={{ background: "#111", border: "1px solid #29251d", borderRadius: 12, overflow: "hidden" }}>
          <h2 style={{ margin: 0, padding: "16px 18px", borderBottom: "1px solid #29251d", fontSize: 16 }}>{text.nodeTable}</h2>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: locale === "ar" ? "right" : "left" }}>
              <thead>
                <tr style={{ color: "#918568", fontSize: 12 }}>
                  <th style={{ padding: 14 }}>NODE</th><th>REGION</th><th>GPU</th><th>TFLOPS</th><th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {nodes.map((node) => (
                  <tr key={node.id} style={{ borderTop: "1px solid #201e19" }}>
                    <td style={{ padding: 14, fontWeight: 700 }}>{node.id}</td>
                    <td>{node.region}</td>
                    <td>{node.gpu}</td>
                    <td style={{ color: "#d4af37" }}>{node.tflops.toFixed(2)}</td>
                    <td><span style={{ color: node.status === "healthy" ? "#7ee7a5" : "#ffb86b" }}>● {node.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article style={{ background: "#111", border: "1px solid #29251d", borderRadius: 12, padding: 18 }}>
          <h2 style={{ marginTop: 0, fontSize: 16, color: "#d4af37" }}>{text.license}</h2>
          <label style={{ display: "block", color: "#9d9279", fontSize: 12, marginBottom: 8 }}>{text.licenseKey}</label>
          <textarea
            value={license}
            onChange={(event) => setLicense(event.target.value)}
            rows={5}
            style={{ width: "100%", boxSizing: "border-box", resize: "vertical", borderRadius: 8, border: "1px solid #3c3524", background: "#090909", color: "#f4ead0", padding: 10 }}
          />
          <button
            type="button"
            onClick={activateLicense}
            style={{ width: "100%", marginTop: 10, border: 0, borderRadius: 8, background: "#d4af37", color: "#17130b", padding: "11px 16px", fontWeight: 800 }}
          >
            {text.activate}
          </button>
          {licenseStatus ? <p style={{ color: "#bcb092", fontSize: 12, lineHeight: 1.5 }}>{licenseStatus}</p> : null}
        </article>
      </section>
    </main>
  );
}
