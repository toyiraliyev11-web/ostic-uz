/**
 * ostic.uz leads -> Google Sheet (Google Apps Script web app).
 *
 * The lead-proxy Worker posts each lead here after sending it to Telegram, so every
 * request is also kept as a row. Requests without the shared secret are ignored.
 *
 * Setup: Extensions > Apps Script in the target Sheet, paste this file, then
 * Project Settings > Script properties: SHARED_SECRET = <a long random string>.
 * Deploy > New deployment > Web app: execute as Me, access: Anyone.
 */
var HEADERS = ['Time', 'Name', 'Company', 'Phone', 'Email', 'Location', 'Direction', 'Project', 'Lang', 'Source'];
var FIELDS = ['name', 'company', 'phone', 'email', 'location', 'direction', 'project', 'lang', 'source'];

function doPost(e) {
  var secret = PropertiesService.getScriptProperties().getProperty('SHARED_SECRET');
  var data;
  try { data = JSON.parse(e.postData.contents); } catch (err) { return reply_(400); }
  if (!secret || data.secret !== secret) return reply_(403);

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  if (sheet.getLastRow() === 0) sheet.appendRow(HEADERS);
  var row = [new Date()].concat(FIELDS.map(function (k) {
    // A leading = + - @ would be run as a formula; keep it as text.
    var v = String(data[k] == null ? '' : data[k]).slice(0, 2500);
    return /^[=+\-@]/.test(v) ? "'" + v : v;
  }));
  sheet.appendRow(row);
  return reply_(200);
}

function reply_(code) {
  return ContentService.createTextOutput(JSON.stringify({ status: code }))
    .setMimeType(ContentService.MimeType.JSON);
}
