
# GitHub Copilot frequently asked questions
Copy as Markdown

- 
				
					
					Copy as Markdown
				
			
- 
				[
					
					View as Markdown
					
				](/docs/agents/agent-troubleshooting/faq.md)
			
- 
- 
				[
					
					Ask in VS Code
				](vscode://GitHub.Copilot-Chat/chat?prompt=Read%20https%3A%2F%2Fcode.visualstudio.com%2Fdocs%2Fagents%2Fagent-troubleshooting%2Ffaq%20and%20answer%20questions%20about%20the%20content.&windowId=_blank)
			
- 
				[
					
					Ask in VS Code Insiders
				](vscode-insiders://GitHub.Copilot-Chat/chat?prompt=Read%20https%3A%2F%2Fcode.visualstudio.com%2Fdocs%2Fagents%2Fagent-troubleshooting%2Ffaq%20and%20answer%20questions%20about%20the%20content.&windowId=_blank)
			

---

Find answers about GitHub Copilot access, usage, chat, agents, inline suggestions, and troubleshooting in Visual Studio Code.
## GitHub Copilot subscription <a id="_github-copilot-subscription"></a>

### Can I use VS Code without signing in? <a id="_can-i-use-vs-code-without-signing-in"></a>

Yes. You don't need an account to use the core editor features in VS Code.
To use AI features, choose one of these access methods:
- Sign in with the GitHub account that has your GitHub Copilot plan. This provides the models, features, and usage allowances included with the plan.
- Configure a [bring-your-own-key model](/docs/agent-customization/language-models#_bring-your-own-language-model-key) for supported chat features without GitHub sign-in.

Some features, including inline suggestions, semantic search, and embeddings, require the GitHub Copilot service and aren't available through bring-your-own-key models.
If you don't want to use AI, you can continue using VS Code without signing in. To hide the built-in AI features, see [Remove AI features from VS Code](/docs/setup/copilot#_remove-ai-features-from-vs-code).
### How can I get a Copilot subscription? <a id="_how-can-i-get-a-copilot-subscription"></a>

There are different ways to get access to GitHub Copilot:
```mermaid
block-beta
columns 2
  h_0["<b>Type of User</b>"]
  h_1["<b>Description</b>"]
  c_0_0["Individual"]
  c_0_1["Set up GitHub Copilot Free to explore basic functionality at no cost with a monthly allowance of inline suggestions a..."]
  c_1_0["Organization/Enterprise member"]
  c_1_1["If you are a member of an organization or enterprise that has a subscription to GitHub Copilot, you can request acces..."]
```

| Type of User | Description |
|---|---|
| Individual | Set up GitHub Copilot Free to explore basic functionality at no cost with a monthly allowance of inline suggestions and AI credits.Sign up for a paid GitHub Copilot plan for more flexibility and access to premium features.See [Setting up GitHub Copilot for yourself](https://docs.github.com/en/copilot/setting-up-github-copilot/setting-up-github-copilot-for-yourself) for all options. |
| Organization/Enterprise member | If you are a member of an organization or enterprise that has a subscription to GitHub Copilot, you can request access to Copilot by going to [https://github.com/settings/copilot](https://github.com/settings/copilot) and requesting access under "Get Copilot from an organization."See [Setting up GitHub Copilot for your organization](https://docs.github.com/en/copilot/setting-up-github-copilot/setting-up-github-copilot-for-your-organization) to enable Copilot for your organization. |


### What's the advantage of signing in with a GitHub account? <a id="_whats-the-advantage-of-signing-in-with-a-github-account"></a>

Signing in with a GitHub account that has access to GitHub Copilot has the following benefits:
- [Higher monthly AI credits allowance](https://docs.github.com/en/copilot/get-started/plans#comparing-copilot-plans)
- [Access to premium language models in chat](https://docs.github.com/en/copilot/reference/ai-models/supported-models#supported-ai-models-per-copilot-plan) beyond auto model selection
- [Bring your own model keys](/docs/agent-customization/language-models#_bring-your-own-language-model-key) (BYOK) to access more models
- [Remote repository indexing and semantic code search](/docs/agents/reference/workspace-context#_semantic-index-sources)
- [Copilot code review](https://docs.github.com/en/copilot/concepts/agents/code-review)
- [Copilot content exclusions](https://docs.github.com/en/copilot/how-tos/configure-content-exclusion/exclude-content-from-copilot)
- [Delegate tasks to the Copilot cloud agent](/docs/agents/run/agent-harnesses#_cloud) for remote execution.

Depending on your Copilot plan, you might have different levels of access and limits. See [GitHub Copilot plans](https://docs.github.com/en/copilot/get-started/plans) for more information.
### How can I monitor my Copilot usage? <a id="_how-can-i-monitor-my-copilot-usage"></a>

You can view the current Copilot usage in the Copilot status dashboard, available through the VS Code Status Bar. The dashboard shows the following information:
- **Inline suggestions**: The percentage of inline suggestions quota you have used in the current month. Paid plans have an unlimited quota for inline suggestions.
- **AI credits**: The percentage of your monthly AI credits allowance you have used in the current month.

Visit the GitHub Copilot documentation for more information about [monitoring usage and entitlements](https://docs.github.com/en/copilot/managing-copilot/monitoring-usage-and-entitlements/monitoring-your-copilot-usage-and-entitlements). For tips on reducing credit consumption, see [optimize AI credit usage](/docs/agents/guides/optimize-usage).
### I reached my inline suggestions or AI credits limit <a id="_i-reached-my-inline-suggestions-or-ai-credits-limit"></a>

Your inline suggestions allowance and AI credits allowance reset every month. If you've only reached the AI credits limit, you can still use inline suggestions. Similarly, if you've reached the limit for inline suggestions, you can still use chat.
For users on Copilot Free, to access more inline suggestions and AI credits, you can sign up for a [paid plan](https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-individuals) directly from VS Code. Alternatively, you can wait until the next month to continue using Copilot for free.
If you're on a paid plan and exhaust your AI credits, you can set a budget for additional usage and keep working, or wait until the next monthly cycle when your allowance resets. Learn more about  in the GitHub Copilot documentation.
For tips on reducing credit consumption, see [optimize AI credit usage](/docs/agents/guides/optimize-usage).
### My Copilot subscription is not detected in VS Code <a id="_my-copilot-subscription-is-not-detected-in-vs-code"></a>

To use your Copilot plan in chat, you must be signed into Visual Studio Code with the GitHub account that has access to the plan.
- If your Copilot subscription is associated with another GitHub account, sign out of your GitHub account and sign in with another account. Use the **Accounts** menu in the Activity Bar for signing out of your current GitHub account. See [Use a different GitHub account with Copilot](/docs/setup/copilot#_use-a-different-github-account-with-copilot) for more information.
- Verify that your Copilot subscription is still active in [GitHub Copilot settings](https://github.com/settings/copilot).
- If you're using a Copilot plan for a managed user account on GHE.com, you need to update some settings before you sign in. See [Using GitHub Copilot with an account on GHE.com](https://docs.github.com/en/copilot/managing-copilot/configure-personal-settings/using-github-copilot-with-an-account-on-ghecom).

### How can I switch accounts for Copilot? <a id="_how-can-i-switch-accounts-for-copilot"></a>

If your Copilot subscription is associated with another GitHub account, sign out of your GitHub account in VS Code, and sign in with another account.
See [Use a different GitHub account with Copilot](/docs/setup/copilot#_use-a-different-github-account-with-copilot) for more information.
## General Copilot questions <a id="_general-copilot-questions"></a>

### How can I remove Copilot from VS Code? <a id="_how-can-i-remove-copilot-from-vs-code"></a>

You can disable the built-in AI features in VS Code with the 
    
      
      chat.disableAIFeatures
      
    
    
        
        
        
    
    
      Open in VS Code
      Open in VS Code Insiders
    
   setting, similar to how you configure other features in VS Code. This disables and hides features like chat or inline suggestions in VS Code and disables the Copilot extensions. You can configure the setting at the workspace or user level.
Alternatively, use the **Learn How to Hide AI Features** action from the Chat menu in the title bar to access the setting.

        
          
          
        
        Note
      
If you have previously disabled the built-in AI features, your choice is respected upon updating to a new version of VS Code.
### Network and firewall configuration for Copilot <a id="_network-and-firewall-configuration-for-copilot"></a>

- Configure your firewall or proxy to permit the domains, ports, and protocols required by GitHub Copilot. See [Troubleshoot firewall settings for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/troubleshooting-firewall-settings-for-github-copilot).
- If you use a corporate VPN or HTTP proxy, check whether Copilot can reach GitHub without connection or certificate errors. See [Troubleshoot network errors for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/troubleshooting-network-errors-for-github-copilot).

To identify a failing connection, [collect network diagnostics](/docs/agents/agent-troubleshooting/troubleshooting#_collect-network-diagnostics).
### My request is rate-limited <a id="_my-request-is-rate-limited"></a>

This error means that the service is temporarily limiting requests. A rate limit can occur even when your monthly AI credits allowance is not exhausted. Wait a few minutes and retry the request.
See [Rate limits for GitHub Copilot](https://docs.github.com/en/copilot/troubleshooting-github-copilot/rate-limits-for-github-copilot) for more information about rate limits and what to do if you are rate limited.
### Are there pre-release builds of the Copilot extensions? <a id="_are-there-pre-release-builds-of-the-copilot-extensions"></a>

Yes, you can switch to the pre-release (nightly) version of a Copilot extension to try the latest features and fixes. From the Extensions view, right-click or select the gear icon to bring up the context menu, and then select **Switch to Pre-Release Version**:
![Extensions view context menu with Switch to Pre-Release Version option](/assets/docs/agents/faq/switch-to-pre-release.png)
You can tell if you're running a pre-release version by the "Pre-release" badge in the extension details:
![Pre-release version of the GitHub Copilot extension](/assets/docs/agents/faq/copilot-ext-pre-release.png)
## Inline suggestions <a id="_inline-suggestions"></a>

### How do I enable or disable inline suggestions? <a id="_how-do-i-enable-or-disable-inline-suggestions"></a>

You can enable or disable inline suggestions in VS Code by using the checkboxes in the Copilot status dashboard from the VS Code Status Bar. You can enable or disable inline suggestions globally or for the file type of the active editor.
![Screenshot showing the VS Code status bar, highlighting the Copilot icon that indicates Copilot is active.](/assets/docs/agents/faq/copilot-disable-completions.png)
Alternatively, use the 
    
      
      github.copilot.enable
      
    
    
        
        
        
    
    
      Open in VS Code
      Open in VS Code Insiders
    
   and 
    
      
      github.copilot.nextEditSuggestions.enabled
      
    
    
        
        
        
    
    
      Open in VS Code
      Open in VS Code Insiders
    
   settings to enable or disable inline suggestions and next edit suggestions, respectively. You can configure these settings at the workspace or user level.
### Inline suggestions are not working in the editor <a id="_inline-suggestions-are-not-working-in-the-editor"></a>

- Verify that [GitHub Copilot is not turned off](#_how-do-i-enable-or-disable-inline-suggestions) globally or for this language.
- Verify that your [GitHub Copilot subscription is active and detected](#_my-copilot-subscription-is-not-detected-in-vs-code).
- Verify that your [network settings](#_network-and-firewall-configuration-for-copilot) permit connectivity to GitHub Copilot.
- Verify that you have not reached the inline suggestions limit for the month with the [Copilot Free plan](https://docs.github.com/copilot/managing-copilot/managing-copilot-as-an-individual-subscriber/about-github-copilot-free).

If these checks pass, [view the GitHub Copilot logs](/docs/agents/agent-troubleshooting/troubleshooting#_view-logs-for-github-copilot).
## Chat and agents <a id="_chat-and-agents"></a>

### Chat features aren't working for me <a id="_chat-features-arent-working-for-me"></a>

Check the following requirements:
- Run **Code: Check for Updates** to update Visual Studio Code.
- If you use a Copilot plan, verify that VS Code is signed in with the GitHub account that has the active plan.
- If you use a bring-your-own-key model, verify the model provider configuration. Some chat features still require the GitHub Copilot service.
- Check the Copilot status dashboard for an exhausted AI credits allowance. If the request reports a temporary rate limit, wait a few minutes and retry it.
- Check your [network and firewall configuration](#_network-and-firewall-configuration-for-copilot).

If these checks pass, follow the [symptom-based troubleshooting steps](/docs/agents/agent-troubleshooting/troubleshooting#_choose-a-troubleshooting-path).
### Agents are not available in chat <a id="_agents-are-not-available-in-chat"></a>

Verify that agents are turned on with the 
    
      
      chat.agent.enabled
      
    
    
        
        
        
    
    
      Open in VS Code
      Open in VS Code Insiders
    
   setting. Your organization can manage this setting with a policy. If the setting is unavailable or managed, contact your administrator.
### What can agents do in VS Code? <a id="_what-can-agents-do-in-vs-code"></a>

Agents handle complete coding tasks autonomously. They plan multi-step implementations, execute coordinated changes across multiple files, run terminal commands, invoke tools, and self-correct when they encounter errors. Use agents for feature implementation, architecture-level refactoring, framework migrations, debugging, and test generation. Learn more about [using agents](/docs/agents/overview).
### Does Copilot work with large codebases and monorepos? <a id="_does-copilot-work-with-large-codebases-and-monorepos"></a>

Yes. VS Code automatically indexes your workspace using semantic search, language intelligence (LSP), and GitHub's code search to provide deep understanding across your repository. For large repositories, [remote indexing](/docs/agents/reference/workspace-context#_semantic-index-sources) uses GitHub's index for fast, comprehensive results across related repositories. Use  to scope context in monorepos, and [custom instructions](/docs/agent-customization/custom-instructions) to describe your project's architecture. See [best practices for large codebases](/docs/agents/best-practices#_work-with-large-codebases).
### Can my organization control AI features and agent access? <a id="_can-my-organization-control-ai-features-and-agent-access"></a>

Yes. Organization administrators can manage Copilot through [enterprise AI settings](/docs/enterprise/manage-ai-settings) and [policies](/docs/enterprise/policies), including enabling or disabling agents, controlling model access, configuring content exclusions, and enforcing trust boundaries. See the [GitHub Copilot Trust Center](https://resources.github.com/copilot-trust-center/) for compliance details.
### Are agents usage-limited? <a id="_are-agents-usage-limited"></a>

Agents consume AI credits from your Copilot plan. Paid plans include a monthly AI credits allowance, and you can set a budget for additional usage if needed. You can run multiple agent sessions in parallel. Users on the free plan have a monthly AI credits allowance. Learn more about [usage-based billing](https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-individuals) and [GitHub Copilot plans](https://docs.github.com/en/copilot/get-started/plans).
### Not all models are available in the language model picker <a id="_not-all-models-are-available-in-the-language-model-picker"></a>

You can choose which models are available in the language model picker. Learn how to [customize the language model picker](/docs/agent-customization/language-models#_customize-the-model-picker).
Organizations can restrict access to certain models. If you believe a model should be available, contact your organization administrator.
### How do I prevent the Chat view from opening automatically? <a id="_how-do-i-prevent-the-chat-view-from-opening-automatically"></a>

By default, the Chat view opens in the Secondary Side Bar. When you close the Chat view for a workspace, VS Code remembers this setting and does not open the Chat view automatically the next time you open that workspace.
You can change the default visibility directly from the Chat view:
1. Open the Chat view (⌃⌘I (Windows, Linux Ctrl+Alt+I)).
2. Select the `...` icon in the top-right corner of the Chat view.
3. Select **Show View by Default** to enable or disable the automatic opening of the Chat view.

You can also control the default visibility of the Secondary Side Bar with the 
    
      
      workbench.secondarySideBar.defaultVisibility
      
    
    
        
        
        
    
    
      Open in VS Code
      Open in VS Code Insiders
    
   setting. Set it to `hidden` to prevent the Chat view from opening automatically.
## Working across Copilot experiences <a id="_working-across-copilot-experiences"></a>

### Can I continue a Copilot CLI or Copilot app session in VS Code? <a id="_can-i-continue-a-copilot-cli-or-copilot-app-session-in-vs-code"></a>

Yes, use **External** \> **All** in the sessions list filter to show [supported sessions from other applications on your machine](/docs/agents/run/sessions/manage-sessions#_view-sessions-from-other-applications) in the Chat view or Agents window. Open a session and send a message to continue it. After you send a message in VS Code, the session is no longer external, so the **External** filter no longer controls whether it appears.
### Why can't I see a Copilot session I already started? <a id="_why-cant-i-see-a-copilot-session-i-already-started"></a>

Sessions from other applications are hidden until you change the [**External** filter](/docs/agents/run/sessions/manage-sessions#_view-sessions-from-other-applications) from **None**. Copilot discovers repository-associated sessions updated within the last seven days. **Recent** shows the two most recently updated external sessions, whereas **All** shows all discovered sessions, not every past session.
### Can I continue a VS Code Copilot session in the terminal? <a id="_can-i-continue-a-vs-code-copilot-session-in-the-terminal"></a>

Yes, open a Copilot session's context menu and select **Resume in Terminal** to continue it with GitHub Copilot CLI. Learn about [using Copilot CLI in the integrated terminal](/docs/agents/run/sessions/manage-sessions#_use-copilot-cli-from-the-terminal).
### Does switching between the Chat view and Agents window start a new session? <a id="_does-switching-between-the-chat-view-and-agents-window-start-a-new-session"></a>

No. When a session supports both interfaces, opening it in either one keeps the same conversation, harness, workspace, and worktree. [Switching surfaces](/docs/agents/concepts/sessions#_sessions-across-surfaces) does not create, fork, or hand off a session.
### Is picking up a session the same as syncing its history? <a id="_is-picking-up-a-session-the-same-as-syncing-its-history"></a>

No, [local session discovery](/docs/agents/run/sessions/manage-sessions#_view-sessions-from-other-applications) lets you continue supported sessions from another application on your machine, while [history sync](/docs/agents/run/sessions/session-history) makes recorded session data available through your GitHub account. Sync is subject to your settings and organization policies and does not by itself provide control over a running agent. For live monitoring or steering from another device, use [remote agent access](/docs/agents/run/remote-agent-sessions) or [Copilot remote control](/docs/agents/run/remote-agent-sessions#_remote-control-copilot-sessions).
## Troubleshooting and feedback <a id="_troubleshooting-and-feedback"></a>

### How can I provide feedback on Copilot? <a id="_how-can-i-provide-feedback-on-copilot"></a>

Use the feedback action associated with an inline suggestion or next edit suggestion. For chat and agent issues, use the VS Code Issue Reporter.
See [Report an unresolved issue](/docs/agents/agent-troubleshooting/troubleshooting#_report-an-unresolved-issue) for the reporting steps, evidence checklist, and precautions for sharing diagnostic data. Follow the [Copilot issue-reporting guidelines](https://github.com/microsoft/vscode/wiki/Copilot-Issues) to make the report actionable.
## Additional resources <a id="_additional-resources"></a>

- [GitHub Copilot Trust Center](https://resources.github.com/copilot-trust-center/)
- [Security considerations for AI in VS Code](/docs/agents/run/security)
- [GitHub Copilot FAQ](https://github.com/features/copilot#faq) in the GitHub documentation
10/14/2026