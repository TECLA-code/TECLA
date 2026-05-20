
// Mode Rhythmic Loop Translation
    } else if (type === 'mode_rhythmic') {
    xmlText = `
    <xml>
      <block type="tecla_repeat_forever" x="50" y="50">
        <statement name="DO">
           <!-- Calculate BPM from Pot Y -->
           <block type="tecla_set_bpm">
             <value name="BPM">
                <block type="tecla_math_map">
                    <value name="VALUE"><block type="tecla_read_pot"><field name="POT">1</field></block></value> <!-- Pot Y -->
                    <value name="FROM_MIN"><shadow type="math_number"><field name="NUM">0</field></shadow></value>
                    <value name="FROM_MAX"><shadow type="math_number"><field name="NUM">127</field></shadow></value>
                    <value name="TO_MIN"><shadow type="math_number"><field name="NUM">60</field></shadow></value>
                    <value name="TO_MAX"><shadow type="math_number"><field name="NUM">180</field></shadow></value>
                </block>
             </value>
             <next>
               <!-- Kick Pattern Logic -->
               <block type="tecla_euclidean_rhythm">
                  <value name="STEP"><block type="tecla_time_millis"></block></value> <!-- Simplification -->
                  <value name="PULSES"><shadow type="math_number"><field name="NUM">4</field></shadow></value>
                  <value name="STEPS"><shadow type="math_number"><field name="NUM">16</field></shadow></value>
               </block>
             </next>
           </block>
        </statement>
      </block>
    </xml>`;
    /* Note to self: The full translation requires variables for step counting, which is complex to generate in raw XML string without visual editor. 
       I will simplify the Rhythmic Mode to a "Modular Rhythm" that emulates the behavior using the new Euclidean block.
    */
    xmlText = `
    <xml>
      <block type="tecla_repeat_forever" x="50" y="50">
        <statement name="DO">
          <block type="controls_if">
            <value name="IF0">
              <block type="tecla_euclidean_rhythm">
                 <value name="STEP">
                   <block type="math_round">
                     <value name="NUM">
                       <block type="math_arithmetic">
                         <field name="OP">DIVIDE</field>
                         <value name="A"><block type="tecla_time_millis"></block></value>
                         <value name="B"><block type="math_number"><field name="NUM">200</field></block></value>
                       </block>
                     </value>
                   </block>
                 </value>
                 <value name="PULSES">
                   <block type="tecla_math_map">
                      <value name="VALUE"><block type="tecla_read_pot"><field name="POT">0</field></block></value>
                      <value name="FROM_MIN"><block type="math_number"><field name="NUM">0</field></block></value>
                      <value name="FROM_MAX"><block type="math_number"><field name="NUM">127</field></block></value>
                      <value name="TO_MIN"><block type="math_number"><field name="NUM">1</field></block></value>
                      <value name="TO_MAX"><block type="math_number"><field name="NUM">8</field></block></value>
                   </block>
                 </value>
                 <value name="STEPS"><block type="math_number"><field name="NUM">8</field></block></value>
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
                 <value name="TIME"><shadow type="math_number"><field name="NUM">0.1</field></shadow></value>
               </block>
            </next>
          </block>
        </statement>
      </block>
    </xml>`;
}
