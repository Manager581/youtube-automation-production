// Tech Joint thumbnails → Photoshop: resize 1280x720, +20% brightness (levels x1.2), Amazon layer on top, save PNG
app.displayDialogs = DialogModes.NO;

var SRC_DOC_NAME = "Untitled-1-Recovered-Recovered-Recovered"; // open tab holding the "Amazon" layer
var OUT_DIR = "/Users/jefflawrence/Documents/youtube-automation-production/assets/techjoint_recreations/photoshop/";
Folder(OUT_DIR).create();

// set by the caller: TJ_JOBS = [[rawPath, outName], ...]
var report = [];
for (var j = 0; j < TJ_JOBS.length; j++) {
  var raw = TJ_JOBS[j][0];
  var outName = TJ_JOBS[j][1];
  try {
    var f = new File(raw);
    if (!f.exists) { report.push(outName + " MISSING:" + raw); continue; }
    var doc = app.open(f);
    // 1) size properly
    doc.resizeImage(UnitValue(1280, "px"), UnitValue(720, "px"), null, ResampleMethod.BICUBIC);
    // 2) brightness +20% (levels: input white 212 -> out = in * 255/212 = x1.20)
    doc.activeLayer = doc.layers[doc.layers.length - 1];
    doc.activeLayer.adjustLevels(0, 212, 1.0, 0, 255);
    // 3) Amazon layer from the open tab, duplicated to TOP of this doc
    var srcDoc = app.documents.getByName(SRC_DOC_NAME);
    app.activeDocument = srcDoc;
    var amazon = srcDoc.artLayers.getByName("Amazon");
    amazon.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
    app.activeDocument = doc;
    // 4) save with corresponding name
    var po = new PNGSaveOptions();
    po.compression = 6;
    po.interlaced = false;
    doc.saveAs(new File(OUT_DIR + outName), po, true, Extension.LOWERCASE);
    doc.close(SaveOptions.DONOTSAVECHANGES);
    report.push(outName + " OK");
  } catch (e) {
    try { if (app.documents.length > 6) app.activeDocument.close(SaveOptions.DONOTSAVECHANGES); } catch (e2) {}
    report.push(outName + " ERROR:" + e.message);
  }
}
report.join(" | ");
