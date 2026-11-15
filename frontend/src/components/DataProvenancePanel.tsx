import type { MissionSite } from '../missionSites';
import type { OfficialSource, TerrainData } from '../types';

type Props = { missionSite: MissionSite; terrain: TerrainData | null; sources: OfficialSource[] };

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return <div className="provenance-field"><span>{label}</span><strong>{value === null || value === undefined || value === '' ? 'Not available in current metadata' : value}</strong></div>;
}

export default function DataProvenancePanel({ missionSite, terrain, sources }: Props) {
  const info = terrain?.coordinate_info ?? {};
  return <section className="provenance-panel">
    <div className="provenance-heading"><div><span className="eyebrow">DATA LINEAGE</span><h3>Data provenance & confidence</h3><p>Trace the sources and limitations behind the active terrain view.</p></div><span className="provenance-stamp">SOURCE-AWARE</span></div>
    <div className="provenance-active">
      <div className="provenance-section-title"><span>ACTIVE TERRAIN PRODUCT</span><b>{terrain ? terrain.status.toUpperCase() : 'NOT LOADED'}</b></div>
      <h4>{missionSite.dem.product}</h4>
      <div className="provenance-grid">
        <Field label="Source organisation" value={missionSite.dem.source}/>
        <Field label="Native product resolution" value={missionSite.dem.resolutionM ? `${missionSite.dem.resolutionM} m / pixel` : null}/>
        <Field label="File format" value={missionSite.dem.format}/>
        <Field label="Loaded grid" value={terrain ? `${terrain.width} × ${terrain.height} cells` : null}/>
        <Field label="Grid cell size" value={terrain ? `${terrain.cell_size_m.toFixed(2)} m` : null}/>
        <Field label="Vertical units" value={terrain?.cell_units}/>
        <Field label="Terrain identifier" value={terrain?.id}/>
        <Field label="Layer provenance" value={terrain?.layer_provenance}/>
      </div>
      <div className="provenance-links"><a href={missionSite.dem.downloadUrl} target="_blank" rel="noreferrer">Original product / download ↗</a><a href={missionSite.dem.documentationUrl} target="_blank" rel="noreferrer">Product documentation ↗</a><a href={missionSite.coordinateSourceUrl} target="_blank" rel="noreferrer">Landing-coordinate reference ↗</a></div>
      <p className="provenance-note">{missionSite.dem.coverageNote}</p>
      {terrain?.warning && <p className="provenance-warning">{terrain.warning}</p>}
    </div>
    <div className="provenance-section-title"><span>COORDINATE & GRID METADATA</span><b>{terrain ? 'RECEIVED' : 'PENDING'}</b></div>
    <div className="provenance-grid">
      <Field label="Reference latitude" value={`${missionSite.latitude.toFixed(5)}°`}/>
      <Field label="Reference longitude east" value={`${missionSite.longitudeEast.toFixed(5)}°E`}/>
      <Field label="Coordinate source" value={missionSite.coordinateSource}/>
      <Field label="Coordinate convention" value={missionSite.coordinateNote}/>
      <Field label="Coordinate metadata" value={Object.keys(info).length ? Object.entries(info).map(([key, value]) => `${key}: ${String(value)}`).join(' · ') : null}/>
      <Field label="NoData mask" value={terrain?.valid_mask ? 'Provided by terrain response' : null}/>
    </div>
    <div className="provenance-caveat"><b>Confidence handling</b><span>Confidence is not estimated from source names alone. The app exposes grid coverage, available masks, explicit uncertainty layers and source limitations; missing metadata stays marked as unavailable.</span></div>
    <div className="provenance-section-title"><span>OFFICIAL DATA-SOURCE REGISTRY</span><b>{sources.length} SOURCES</b></div>
    <div className="provenance-source-list">{sources.map((source) => <article className="provenance-source" key={source.id}>
      <div><strong>{source.name}</strong><span>{source.organization} · {source.kind.replace(/_/g,' ').toUpperCase()}</span></div>
      <em className={source.integration === 'connected' ? 'connected' : ''}>{source.integration.replace(/_/g,' ')}</em>
      <p>{source.description}</p>
      <div className="provenance-source-meta"><span>{source.format}</span><span>{source.availability.replace(/_/g,' ')}</span></div>
      <p className="provenance-limit"><b>Coverage / limits:</b> {source.coverage} {source.limitations}</p>
      <div className="provenance-links"><a href={source.url} target="_blank" rel="noreferrer">Source endpoint ↗</a><a href={source.documentation} target="_blank" rel="noreferrer">Documentation ↗</a></div>
    </article>)}</div>
  </section>;
}

