# 🧪 **Complete CLI Testing Guide for SandStrike**

## **📋 Quick Testing Workflow**

### **Step 1: Check Available Sessions**
```bash
# List all sessions to get session IDs
sandstrike sessions list --source file

# Example output will show session IDs like:
# scan_2025-09-12_16:17:3
# sample_yaml_security_sc
```

### **Step 2: Generate HTML Reports (Pro Users Only)**
```bash
# Generate overview HTML report
sandstrike reports overview --session-id "scan_2025-09-12_16:17:3"

# Generate detailed HTML report
sandstrike reports detailed --session-id "scan_2025-09-12_16:17:3"

# Generate executive HTML report
sandstrike reports executive --session-id "scan_2025-09-12_16:17:3"

# Generate all three report types at once
sandstrike reports all --session-id "scan_2025-09-12_16:17:3"
```

### **Step 3: Verify HTML Files**
```bash
# Check reports folder for generated HTML files
dir sandstrike\reports\*.html

# You should see files like:
# overview_20250103_110310.html
# detailed_20250103_110310.html
# executive_20250103_110310.html
```

## **🔧 Complete Command Reference**

### **📊 Reports Commands (Pro Users Only)**

#### **Generate All Reports at Once**
```bash
# Generate all three report types at once
sandstrike reports all

# Generate all reports for specific sessions
sandstrike reports all --session-id "session1,session2"

# Generate all reports from specific source
sandstrike reports all --source file

# Generate all reports with custom prefix
sandstrike reports all --output my-report-prefix
```

#### **Overview Report**
```bash
# Generate overview HTML report with specific sessions
sandstrike reports overview --session-id "session1,session2"

# Generate overview HTML report with all sessions (default behavior)
sandstrike reports overview

# Generate overview HTML report from specific source
sandstrike reports overview --source local
sandstrike reports overview --source file

# Generate overview HTML report with custom output prefix
sandstrike reports overview --output "my-overview"
```

#### **Detailed Report**
```bash
# Generate detailed HTML report with specific sessions
sandstrike reports detailed --session-id "session1,session2"

# Generate detailed HTML report with all sessions (default behavior)
sandstrike reports detailed

# Generate detailed HTML report from specific source
sandstrike reports detailed --source local
sandstrike reports detailed --source file

# Generate detailed HTML report with custom output prefix
sandstrike reports detailed --output "detailed"
```

#### **Executive Report**
```bash
# Generate executive HTML report with specific sessions
sandstrike reports executive --session-id "session1,session2"

# Generate executive HTML report with all sessions (default behavior)
sandstrike reports executive

# Generate executive HTML report from specific source
sandstrike reports executive --source local
sandstrike reports executive --source file

# Generate executive HTML report with custom output prefix
sandstrike reports executive --output "executive-summary"
```

### **📋 Sessions Commands (To Get Session IDs)**

```bash
# List all sessions
sandstrike sessions list

# List sessions from local storage
sandstrike sessions list --source local

# List sessions from file storage
sandstrike sessions list --source file

# Filter by status
sandstrike sessions list --status completed
sandstrike sessions list --status failed
sandstrike sessions list --status cancelled

# View session details
sandstrike sessions show SESSION_ID

# View session with detailed prompt/response info
sandstrike sessions show SESSION_ID --detailed

# Get help for sessions commands
sandstrike sessions --help
sandstrike sessions list --help
```

### **🖥️ Running Scans (Web UI Only)**

**Note:** Scan functionality is available exclusively through the Web UI. To run security scans:

```bash
# Start the web interface
sandstrike ui start

# Then navigate to http://localhost:3000/scan in your browser
```

The Web UI provides:
- **Local Scan**: Test Ollama models at specified endpoints
- **Public API Scan**: Test public API endpoints
- **Collection Selection**: Choose which prompt collections to test
- **Grader Configuration**: Configure AI-powered response evaluation
- **Real-time Progress**: Monitor scan progress in real-time

## **🎯 Testing Scenarios**

### **Scenario 1: Basic Report Generation**
```bash
# 1. List sessions
sandstrike sessions list --source file

# 2. Generate overview report
sandstrike reports overview --session-id "SESSION_ID_FROM_STEP_1"

# 3. Check generated HTML
dir sandstrike\reports\*.html
```

### **Scenario 2: Comprehensive Testing (Using Web UI for Scans)**
```bash
# 1. Start web UI and run a scan via browser
sandstrike ui start
# Navigate to http://localhost:3000/scan and run a test

# 2. List sessions to get the new session ID
sandstrike sessions list --source local

# 3. Generate all three report types
sandstrike reports all --session-id "NEW_SESSION_ID"

# 4. Verify all HTML reports were created
dir sandstrike\reports\*.html
```

### **Scenario 3: Custom Output Testing**
```bash
# Generate reports with custom prefix (creates prefix_overview.html, etc.)
sandstrike reports all --session-id "session1" --output "custom-report"

# Or generate individual reports with custom prefix
sandstrike reports overview --session-id "session1" --output "my-overview"
sandstrike reports detailed --session-id "session1" --output "my-detailed"
sandstrike reports executive --session-id "session1" --output "my-executive"
```

## **📁 Expected Output**

### **HTML Files Generated**
- `overview_YYYYMMDD_HHMMSS.html`
- `detailed_YYYYMMDD_HHMMSS.html`
- `executive_YYYYMMDD_HHMMSS.html`

### **HTML Content Structure**
1. **Professional Design** - Avenlis branding and responsive layout
2. **Tabbed Interface** - Preface and Results sections
3. **Interactive Charts** - Chart.js visualizations
4. **Comprehensive Metrics** - Success/failure rates and session performance
5. **Vulnerability Analysis** - By category, attack technique, and compliance frameworks
6. **Top 10 Analysis** - Attack techniques and vulnerability categories
7. **Compliance Tracking** - OWASP Top 10 LLM and MITRE ATLAS frameworks
8. **Session Insights** - Detailed prompt analysis and results

## **🔧 Troubleshooting**

### **Common Issues**
```bash
# If "No valid sessions selected" error:
# 1. Check session IDs are correct
sandstrike sessions list --source file

# 2. Use exact session IDs from the list
sandstrike reports overview --session-id "EXACT_SESSION_ID"

# If report generation fails:
# 1. Check your API key is set
sandstrike auth verify

# 2. Check reports folder exists
dir sandstrike\reports\

# 3. Ensure you have a Pro subscription for reports feature
```

### **Help Commands**
```bash
# Get help for any command
sandstrike --help
sandstrike reports --help
sandstrike sessions --help
sandstrike prompts --help
sandstrike collections --help
sandstrike targets --help
```

## **✅ Success Indicators**

- ✅ PDF files created in `avenlis/reports/` folder
- ✅ Professional cover page with branding
- ✅ Table of contents with page numbers
- ✅ Executive summary with metrics
- ✅ Charts and visualizations
- ✅ Session details table
- ✅ Vulnerability analysis
- ✅ Security recommendations
- ✅ Professional formatting throughout

## **📁 Collections Testing**

### **Collection Management**
```bash
# Test creating collections with required source parameter
sandstrike collections create --name "Test Collection" --description "Testing collections" --source local
sandstrike collections create --name "File Collection" --description "Testing file storage" --source file

# Test listing collections (should show source column)
sandstrike collections list
sandstrike collections list --source file
sandstrike collections list --source local

# Test adding prompts to collections
sandstrike collections add-prompt --collection-id COLLECTION_ID --collection-source local --prompt-ids prompt1,prompt2 --prompt-source file

# Test removing prompts from collections
sandstrike collections remove-prompt --collection-id COLLECTION_ID --collection-source local --prompt-ids prompt1

# Test deleting collections (should require confirmation)
sandstrike collections delete COLLECTION_ID
```

### **Expected Results**
- ✅ Collections created with correct source type
- ✅ List shows "Source" column with "File" or "Local" values
- ✅ Add-prompt successfully adds prompts to collection
- ✅ Remove-prompt successfully removes prompts from collection  
- ✅ Delete command requires confirmation

## **🗄️ Database Management Testing**

### **Database Status**
```bash
# Test database status command
sandstrike database status
```

### **Database Cleanup**
```bash
# Test dry run (preview only)
sandstrike database local-wipe --dry-run

# Test actual cleanup (requires confirmation)
sandstrike database local-wipe
```

### **Expected Results**
- ✅ Status shows table categorization (Required, Redundant, Unknown)
- ✅ `dynamic_variables` table listed as "Required"
- ✅ Dry run shows what would be removed
- ✅ Actual cleanup requires confirmation
- ✅ Essential tables preserved after cleanup

## **🔧 Dynamic Variables Testing**

### **Basic Variable Management**
```bash
# Test listing variables
sandstrike variables list --source all
sandstrike variables list --source local
sandstrike variables list --source file

# Test setting variables
sandstrike variables set --category application --name test_app --value "TestApp" --source local
sandstrike variables set --category data --name test_data --value "test information" --source file
sandstrike variables set --category system --name test_system --value "test environment" --source local

# Test listing variables by category
sandstrike variables list --category application
sandstrike variables list --category data
sandstrike variables list --category system

# Test updating variables
sandstrike variables update --category application --name test_app --value "UpdatedTestApp" --source local
sandstrike variables update --category data --name test_data --value "updated information" --source file
```

### **Expected Output**
- ✅ Variables should be listed correctly from both sources
- ✅ Setting variables should return success messages
- ✅ Listing by category should show all variables in that category
- ✅ Updating variables should show old and new values

## **🎯 Targets Testing**

### **Target Management**
```bash
# Test creating targets
sandstrike targets create --id target_001 --name "Local Ollama" --ip "http://localhost:11434" --source local
sandstrike targets create --id target_002 --name "Ollama Model" --ip "http://localhost:11434" --type Ollama --model llama3.2:1b --source file

# Test listing targets
sandstrike targets list
sandstrike targets list --source local
sandstrike targets list --source file

# Test viewing targets
sandstrike targets view --target-ids target_001 --source local

# Test deleting targets
sandstrike targets delete --target-ids target_001 --source local
```

### **Expected Results**
- ✅ Targets created with correct source type
- ✅ List shows all targets with source column
- ✅ View shows detailed target information
- ✅ Delete requires confirmation

---

**🎉 Happy Testing!** Use these commands to thoroughly test your beautiful HTML reports!
