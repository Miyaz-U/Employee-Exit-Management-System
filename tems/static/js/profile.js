document.addEventListener("DOMContentLoaded", function () {
    const profileBtn = document.getElementById("profile-btn");
    const hrApprovalsLink = document.getElementById("hr-approvals-link");
    const managerApprovalsLink = document.getElementById("manager-approvals-link");
    const itApprovalsLinkEmail = document.getElementById("it-approvals-link-email");
    const itApprovalsLinkAsset = document.getElementById("it-approvals-link-asset");
    const financeApprovalsLink = document.getElementById("finance-approvals-link");
    const exitButton = document.getElementById("exit-button");

    const hrSection = document.getElementById("hr-approvals-section");
    const managerSection = document.getElementById("manager-approvals-section");
    const itSectionEmail = document.getElementById("it-approvals-section-email");
    const itSectionAsset = document.getElementById("it-approvals-section-asset");
    const financeSection = document.getElementById("finance-approvals-section");

    function hideAllSections() {
        if (hrSection) hrSection.style.display = "none";
        if (managerSection) managerSection.style.display = "none";
        if (itSectionEmail) itSectionEmail.style.display = "none";
        if (itSectionAsset) itSectionAsset.style.display = "none";
    }

    if (profileBtn) {
        profileBtn.addEventListener("click", function () {
            hideAllSections();
            document.getElementById("profile-content").style.display = "block";
        });
    }

    if (hrApprovalsLink) {
        hrApprovalsLink.addEventListener("click", function (e) {
            e.preventDefault();
            hideAllSections();
            if (hrSection) hrSection.style.display = "block";
        });
    }

    if (managerApprovalsLink) {
        managerApprovalsLink.addEventListener("click", function (e) {
            e.preventDefault();
            hideAllSections();
            if (managerSection) managerSection.style.display = "block";
        });
    }

    if (itApprovalsLinkEmail) {
        itApprovalsLinkEmail.addEventListener("click", function (e) {
            e.preventDefault();
            hideAllSections();
            if (itSectionEmail) itSectionEmail.style.display = "block";
        });
    }

    if (itApprovalsLinkAsset) {
        itApprovalsLinkAsset.addEventListener("click", function (e) {
            e.preventDefault();
            hideAllSections();
            if (itSectionAsset) itSectionAsset.style.display = "block";
        });
    }

    if (exitButton) {
        exitButton.addEventListener("click", function () {
            window.location.href = "/initiate_resignation/";
        });
    }

    if (financeApprovalsLink) {
        financeApprovalsLink.addEventListener("click", function (e) {
            e.preventDefault();
            hideAllSections();
            if (financeSection) financeSection.style.display = "block";
        });
    }
});
