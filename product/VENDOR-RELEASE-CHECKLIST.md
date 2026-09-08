# Vendor Release Checklist

Before shipping a customer build:

- [ ] Replace `YOUR COMPANY NAME` and support address.
- [ ] Configure the vendor Ed25519 public key used for license verification.
- [ ] Run dependency/license/SBOM audit.
- [ ] Run container vulnerability scan.
- [ ] Run unit + end-to-end tests on supported OS versions.
- [ ] Build and test the exact customer installer artifact.
- [ ] Sign the installer/scripts/container metadata using the vendor's release infrastructure.
- [ ] Generate release checksums.
- [ ] Create customer-specific license and configuration.
- [ ] Validate model against customer acceptance criteria.
- [ ] Complete commissioning and rollback drill.
