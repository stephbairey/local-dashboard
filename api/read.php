<?php
// api/read.php — serve JSON from /data with no caching
header("Content-Type: application/json; charset=utf-8");
header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Pragma: no-cache");
header("Expires: 0");

$allowed = ["calendar.json","weather.json","tides.json","moon.json","sun.json","gc.json","bank.json"];
$file = isset($_GET["file"]) ? basename($_GET["file"]) : "";
if (!in_array($file, $allowed, true)) {
  http_response_code(400);
  echo json_encode(["error" => "invalid file"]);
  exit;
}

$path = __DIR__ . "/../data/" . $file;
if (!is_file($path)) {
  http_response_code(404);
  echo json_encode(["error" => "not found"]);
  exit;
}

readfile($path);


