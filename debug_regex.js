const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'LIVE_GENERATIVE.py');
console.log('Reading file:', filePath);

try {
    const fileData = fs.readFileSync(filePath, 'utf8');
    console.log('File length:', fileData.length);
    console.log('First 100 chars:', fileData.substring(0, 100));
    console.log('Last 200 chars:', fileData.substring(fileData.length - 200));

    // Regex tolerant a espais " = " o "="
    const regex = /TECLA_BLOCKS_EMBEDDED_JSON\s*=\s*'''([\s\S]+?)'''/;
    const embeddedMatch = fileData.match(regex);

    if (embeddedMatch) {
        console.log('✅ Regex MATCHED!');
        console.log('Extracted length:', embeddedMatch[1].length);
        
        try {
            const json = JSON.parse(embeddedMatch[1]);
            console.log('✅ JSON Parse SUCCESS!');
            console.log('Blocks found:', json.blocks ? 'YES' : 'NO');
        } catch (e) {
            console.error('❌ JSON Parse FAILED:', e.message);
            console.log('Extracted string start:', embeddedMatch[1].substring(0, 50));
        }
    } else {
        console.error('❌ Regex DID NOT MATCH');
        // Check if the marker exists at all
        const idx = fileData.indexOf('TECLA_BLOCKS_EMBEDDED_JSON');
        if (idx !== -1) {
            console.log('Marker found at index:', idx);
            console.log('Context around marker:', fileData.substring(idx, idx + 50));
        } else {
            console.log('Marker TECLA_BLOCKS_EMBEDDED_JSON NOT FOUND in file.');
        }
    }

} catch (e) {
    console.error('Error reading file:', e);
}
