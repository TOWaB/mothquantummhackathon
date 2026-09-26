"""The artifact page.

Test it without touching app.py or the live state:

    python tools/seed_artifact.py state/versions.test.json
    ARTIFACT_VERSIONS=state/versions.test.json python test_artifact.py

Wire it into the real app only once someone else has stopped editing app.py:

    from artifact import bp
    app.register_blueprint(bp)

Reads state/versions.json and nothing else. No API calls, no credits, no key.
Renders with JavaScript disabled, because it is going on phones on a venue network.
"""
import json, os, pathlib
from flask import Blueprint, abort, render_template_string, url_for

bp = Blueprint("artifact", __name__)

# Point at a throwaway file while testing so the live state is never touched:
#   ARTIFACT_VERSIONS=state/versions.test.json
VERSIONS = pathlib.Path(os.environ.get("ARTIFACT_VERSIONS", "state/versions.json"))


def find(token):
    if not VERSIONS.exists():
        return None
    for versions in json.loads(VERSIONS.read_text()).values():
        for v in versions:
            if v.get("token") == token:
                return v
    return None


@bp.get("/a/<token>")
def artifact(token):
    v = find(token)
    if not v:
        abort(404)                      # an unknown token is not the current state
    return render_template_string(PAGE, v=v)


PAGE = """<!doctype html>
<html lang="en-GB"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Side {{ v.face }}, version {{ v.v }}</title>
<meta property="og:title" content="Side {{ v.face }}, version {{ v.v }}">
<meta property="og:description" content="Changed at the Quantum Dodecahedron. {{ v.flips|length }} flips on Atlas, job {{ v.job_id[:8] }}.">
<meta property="og:image" content="{{ '/' + v.file }}">
<meta name="twitter:card" content="summary_large_image">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;600;700&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>
:root{--paper:#fff;--ink:#141414;--signal:#f0f22e;--circuit:#4634e0;
 --slate:#6a696d;--steel:#7b7d86;--mist:#d3d6d8;color-scheme:light}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
 font-family:"Inter Tight",system-ui,Arial,sans-serif;font-size:15px;line-height:1.45;
 padding:calc(18px + env(safe-area-inset-top,0px)) 16px calc(40px + env(safe-area-inset-bottom,0px))}
.w{max-width:560px;margin:0 auto}
.k{font-family:"JetBrains Mono",monospace;font-size:9.5px;text-transform:uppercase;
 letter-spacing:.1em;color:var(--steel)}
.sq{width:9px;height:9px;background:var(--signal);outline:1px solid var(--ink);display:inline-block}
h1{font-size:26px;font-weight:700;letter-spacing:-.03em;margin:10px 0 4px}
.sub{margin:0 0 14px;font-size:13px;color:var(--slate)}
img{width:100%;border:1px solid var(--mist);border-radius:8px;display:block;background:#000}
h2{font-size:13px;font-weight:600;margin:20px 0 6px;border-top:2px solid var(--ink);padding-top:10px}
.r{display:grid;grid-template-columns:1fr auto;gap:10px;padding:5px 0;
 border-bottom:1px solid var(--mist);font-size:12.5px;align-items:baseline}
.r:last-child{border-bottom:0}
.r .a{color:var(--slate)}
.r .a em{display:block;font-style:normal;font-family:"JetBrains Mono",monospace;
 font-size:9px;color:var(--steel)}
.r .b{font-weight:600;font-size:11.5px;text-align:right;word-break:break-all}
.r .b.c{color:var(--circuit);font-family:"JetBrains Mono",monospace;font-weight:400;font-size:10px}
.f{display:grid;grid-template-columns:44px 46px 20px 1fr;gap:8px;align-items:center;
 padding:5px 0;border-bottom:1px solid var(--mist);font-size:12px}
.f .n{color:var(--steel);font-size:11px}
.f .o{font-weight:600}
.f .bit{font-family:"JetBrains Mono",monospace;text-align:center;background:#f0f0f1;border-radius:3px}
.f .bit.one{background:var(--ink);color:#fff}
.f .j{font-family:"JetBrains Mono",monospace;font-size:9.5px;color:var(--circuit);
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.d{margin:8px 0 0;font-size:12.5px}
.d .bits{font-family:"JetBrains Mono",monospace;letter-spacing:.28em;font-weight:500}
.d .good{background:linear-gradient(transparent 58%,var(--signal) 58%);font-weight:600}
footer{margin-top:26px;border-top:1px solid var(--mist);padding-top:10px}
</style></head><body><div class="w">

<span class="k"><i class="sq"></i> Visual Hive &nbsp; Quantum Dodecahedron</span>
<h1>Side {{ v.face }}, version {{ v.v }}</h1>
<p class="sub">This is how side {{ v.face }} looked when you changed it. It has moved on since.</p>

<img src="{{ '/' + v.file }}" alt="Side {{ v.face }}, version {{ v.v }}">

<h2>Your flips</h2>
{% for f in v.flips %}
<div class="f">
  <span class="n">Flip {{ loop.index0 % 4 + 1 }}</span>
  <span class="o">{{ f.output }}</span>
  <span class="bit{% if f.bit %} one{% endif %}">{{ f.bit }}</span>
  <span class="j">{{ f.job_id[:8] }} · ibm {{ f.ibm_job_id[:16] }}</span>
</div>
{% endfor %}
{% for d in v.draws %}
<p class="d"><span class="bits">{{ d.bits|join(' ') }}</span> is {{ d.idx }}.
{% if d.accepted %}Counting from zero, that is <span class="good">side {{ d.idx + 1 }}</span>.
{% else %}Only 12 sides, so it went and we drew again.{% endif %}</p>
{% endfor %}

<h2>How it was made</h2>
<div class="r"><span class="a">First photo<em>subject</em></span><span class="b">{{ v.subject }}</span></div>
<div class="r"><span class="a">Second photo<em>opposite</em></span><span class="b">{{ v.opposite }}</span></div>
<div class="r"><span class="a">How much mixing<em>strength</em></span><span class="b">{{ v.params.strength }}</span></div>
<div class="r"><span class="a">Which way it mixes<em>direction</em></span><span class="b">{{ v.params.direction }}</span></div>
<div class="r"><span class="a">How wide it spreads<em>mask_radius</em></span><span class="b">{{ v.params.mask_radius }}</span></div>
<div class="r"><span class="a">How much got through<em>floor</em></span><span class="b">{{ v.floor }}</span></div>
<div class="r"><span class="a">Job<em>job_id</em></span><span class="b c">{{ v.job_id }}</span></div>
<div class="r"><span class="a">Took<em>elapsed_s</em></span><span class="b">{{ v.elapsed_s }}s</span></div>

<footer><span class="k">{{ v.ts[:19].replace('T',' ') }} &nbsp;·&nbsp; backend aer · mode emu</span></footer>
</div></body></html>
"""
