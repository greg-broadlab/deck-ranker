const CONFIG = {
    supabase_url: 'https://kznfnzhttmgidgicjeyx.supabase.co',
    supabase_key: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt6bmZuemh0dG1naWRnaWNqZXl4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MTQ0MjEsImV4cCI6MjA5NjQ5MDQyMX0.iUqkUFFKP7rJXFOTw9Tu0DRAAZuyXQ_gmZl8PoBGHoQ',
    cloudinary_cloud: 'dtm0s452r',
    categories: {
        intro: 'Intro',
        rtb: 'RTB',
        optimisation: 'Optimisation',
        eoc: 'EOC',
        qbr: 'QBR',
    }
};

// Supabase REST helpers
const SB = {
    headers: {
        'apikey': CONFIG.supabase_key,
        'Authorization': `Bearer ${CONFIG.supabase_key}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    },
    url: (path) => `${CONFIG.supabase_url}/rest/v1${path}`,

    async get(path) {
        const r = await fetch(SB.url(path), { headers: SB.headers });
        return r.json();
    },
    async post(path, body) {
        const r = await fetch(SB.url(path), {
            method: 'POST', headers: SB.headers, body: JSON.stringify(body)
        });
        return r.json();
    },
    async patch(path, body) {
        await fetch(SB.url(path), {
            method: 'PATCH',
            headers: { ...SB.headers, 'Prefer': 'return=minimal' },
            body: JSON.stringify(body)
        });
    },
};

function slideUrl(prefix, n) {
    return `https://res.cloudinary.com/${CONFIG.cloudinary_cloud}/image/upload/${prefix}/${n}.png`;
}

// ELO
const K = 32;
function expected(a, b) { return 1 / (1 + Math.pow(10, (b - a) / 400)); }
function calcElo(winnerElo, loserElo) {
    return {
        winner: Math.round(winnerElo + K * (1 - expected(winnerElo, loserElo))),
        loser:  Math.round(loserElo  + K * (0 - expected(loserElo, winnerElo))),
    };
}
