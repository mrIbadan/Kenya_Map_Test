# Add a comprehensive sidebar with legends and summary
sidebar_html = '''
<div style="position: fixed; 
     top: 50px; right: 50px; width: 250px; 
     border:2px solid grey; z-index:9999; font-size:14px; 
     background-color:white; padding: 15px; border-radius: 5px;
     box-shadow: 3px 3px 5px grey;">
     <h3 style="text-align: center; margin-top: 0;">Cyber Attack Dashboard</h3>
     
     <hr>
     <h4 style="margin-bottom: 5px;">Heatmap Intensity</h4>
     <p style="font-size: 12px; margin-top: 0;">Shows attack density and severity combined</p>
     <div style="display: flex; margin-bottom: 10px;">
         <div style="flex-grow: 1; height: 15px; background: linear-gradient(to right, blue, lime, yellow, orange, red);"></div>
     </div>
     <div style="display: flex; justify-content: space-between; font-size: 12px;">
         <span>Low</span>
         <span>Medium</span>
         <span>High</span>
     </div>
     
     <hr>
     <h4 style="margin-bottom: 5px;">Attack Types</h4>
     <ul style="padding-left: 20px; margin-top: 5px;">
        <li>DDoS</li>
        <li>Phishing</li>
        <li>Ransomware</li>
        <li>Credential Stuffing</li>
     </ul>
     
     <hr>
     <h4 style="margin-bottom: 5px;">Severity Legend</h4>
     <div style="display: flex; align-items: center; margin-bottom: 3px;">
         <div style="background: blue; width: 15px; height: 15px; margin-right: 8px;"></div>
         <span>Low Risk (1-3)</span>
     </div>
     <div style="display: flex; align-items: center;">
         <div style="background: red; width: 15px; height: 15px; margin-right: 8px;"></div>
         <span>High Risk (4-5)</span>
     </div>
     
     <hr>
     <h4 style="margin-bottom: 5px;">Risk Summary</h4>
     <div id="risk-summary" style="font-size: 12px;">
        <!-- Summary will be inserted here by JavaScript -->
     </div>
</div>

<script>
document.getElementById("risk-summary").innerHTML = `
    <ul style="padding-left: 15px; margin-top: 5px;">
        <li><strong>Northern Hemisphere:</strong> 200 attacks, 3.0 severity</li>
        <li><strong>Equatorial Region:</strong> 143 attacks, 3.15 severity</li>
        <li><strong>Southern Hemisphere:</strong> 157 attacks, 2.9 severity</li>
    </ul>
    <p><strong>Highest Risk:</strong> Equatorial areas with concentrated ransomware activity</p>
`;
</script>
'''

map_folium.get_root().html.add_child(folium.Element(sidebar_html))
