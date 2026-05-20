
// Additional Example Logic for Complex Synth
if (type === 'complex_synth') {
    xmlText = `
    <xml>
      <block type="tecla_repeat_forever" x="50" y="50">
        <statement name="DO">
           <!-- Generative Melody Line -->
           <block type="tecla_probability">
             <value name="PERCENT"><shadow type="math_number"><field name="NUM">70</field></shadow></value>
             <statement name="DO">
               <!-- LFO Controls Pitch -->
               <block type="tecla_play_note">
                 <value name="NOTE">
                    <block type="tecla_scale_quantize">
                        <field name="SCALE">minor</field>
                        <field name="ROOT">C</field>
                        <value name="VALUE">
                            <block type="tecla_software_lfo">
                                <value name="RATE"><shadow type="math_number"><field name="NUM">0.5</field></shadow></value>
                                <value name="MIN"><shadow type="math_number"><field name="NUM">48</field></shadow></value>
                                <value name="MAX"><shadow type="math_number"><field name="NUM">72</field></shadow></value>
                            </block>
                        </value>
                    </block>
                 </value>
                 <value name="VELOCITY"><shadow type="math_number"><field name="NUM">100</field></shadow></value>
                 <value name="DURATION"><shadow type="math_number"><field name="NUM">0.2</field></shadow></value>
               </block>
             </statement>
             <next>
                <!-- Euclidean Rhythm Kick -->
                <block type="controls_if">
                    <value name="IF0">
                        <block type="tecla_euclidean_rhythm">
                            <value name="STEP">
                                <block type="tecla_time_millis"></block> <!-- Hacky step using time, better with counter -->
                            </value>
                            <value name="PULSES"><shadow type="math_number"><field name="NUM">5</field></shadow></value>
                            <value name="STEPS"><shadow type="math_number"><field name="NUM">16</field></shadow></value>
                        </block>
                    </value>
                    <statement name="DO0">
                        <block type="tecla_play_note">
                            <value name="NOTE"><shadow type="math_number"><field name="NUM">36</field></shadow></value>
                            <value name="VELOCITY"><shadow type="math_number"><field name="NUM">120</field></shadow></value>
                            <value name="DURATION"><shadow type="math_number"><field name="NUM">0.1</field></shadow></value>
                        </block>
                    </statement>
                    <next>
                        <block type="tecla_wait">
                            <value name="TIME"><shadow type="math_number"><field name="NUM">0.25</field></shadow></value>
                        </block>
                    </next>
                </block>
             </next>
           </block>
        </statement>
      </block>
    </xml>`;
}
