import "./globals.css";

export const metadata = {
  title: "Nerf Recon Web",
  description: "Upload a video → reconstruct with Nerfstudio → export renders and geometry."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="container">
          <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", gap:12, flexWrap:"wrap"}}>
            <div>
              <div style={{fontSize:22, fontWeight:800}}>Nerf Recon Web</div>
              <div className="small">Upload → Choose model → Reconstruct → Download outputs</div>
            </div>
            <a className="badge" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API docs</a>
          </div>
          <hr />
          {children}
          <hr />
          <div className="small">Local-first. Needs NVIDIA GPU for best results.</div>
        </div>
      </body>
    </html>
  );
}
