const { spawn } = require("child_process");
const path = require("path");

const server = path.join(__dirname, "..", "..", "workers", "mcp", "src", "stdio.js");
const docsRoot = path.join(__dirname, "..", "..", "docs");
const child = spawn("node", [server], {
  env: { ...process.env, ERISPULSE_DOCS_DIR: docsRoot },
  stdio: ["pipe", "pipe", "pipe"],
  cwd: __dirname,
});

let output = "";
function flushLines() {
  let idx;
  while ((idx = output.indexOf("\n")) >= 0) {
    const line = output.slice(0, idx);
    output = output.slice(idx + 1);
    if (!line.trim()) continue;
    handleLine(line.trim());
  }
}
function handleLine(line) {
  try {
    const msg = JSON.parse(line);
    if (msg.method === undefined && msg.id !== undefined) {
      onResponse(msg);
    }
  } catch (e) {}
}
let pendingId = 0;
let step = 0; // 0=init 1=tools/list 2=call
function send(method, params) {
  child.stdin.write(JSON.stringify({ jsonrpc: "2.0", id: ++pendingId, method, params }) + "\n");
}

function onResponse(resp) {
  const r = resp.result || {};
  if (step === 0) {
    console.log("initialize:", "serverInfo:" + (r.serverInfo ? r.serverInfo.name + " v" + r.serverInfo.version : "?"));
    step = 1;
    return send("tools/list", {});
  }
  if (step === 1) {
    console.log("tools:", r.tools.map((t) => t.name).join(", "));
    step = 2;
    return send("tools/call", { name: "search_docs", arguments: { query: "命令注册 事件监听" } });
  }
  if (step === 2 && r.content && r.content[0]) {
    console.log("tools/call result (first 220):");
    console.log(r.content[0].text.slice(0, 220).replace(/\n/g, " "));
    console.log("...");
    console.log("STDIO TEST OK");
    child.kill();
    process.exit(0);
  }
  console.error("unexpected response:", JSON.stringify(resp).slice(0, 200));
  child.kill();
  process.exit(1);
}

child.stderr.on("data", (d) => process.stderr.write(d));
child.stdout.on("data", (d) => {
  output += d.toString();
  flushLines();
});
child.on("exit", (code) => {
  if (!parseDone) {
    console.error("server exited before response, code:", code);
    process.exit(1);
  }
});

setTimeout(() => {
  console.error("TIMEOUT");
  child.kill();
  process.exit(1);
}, 10000);

send("initialize", {});