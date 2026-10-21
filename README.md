# Off On Our Own

The live travel journal at **https://offonourown.co.uk/** is built with Hugo and published through GitHub Actions / GitHub Pages.

## Local development

Install [Hugo](https://gohugo.io/installation/) and run:

```bash
hugo server --disableFastRender
```

Hugo's site URL and the deployment workflow use the custom domain, not the previous \`/OffOnOurOwn/\` project-site prefix. The Pages custom domain must also be set to \`offonourown.co.uk\` under GitHub repository Settings > Pages.

## Images and imported WordPress posts

The repository contains **post content but not the original photograph files**. Images originally uploaded to WordPress need to be available separately on \`https://photos.offonourown.co.uk/\`, preserving their original \`year/month/filename\` paths. This hostname must have working DNS, HTTPS and an accessible media store. Changing the domain's DNS or nameservers can disrupt the \`photos\` subdomain even if the main website works.

During rendering Hugo now rewrites both the original \`/wp-content/uploads/\` links and absolute WordPress upload URLs to the photo hostname. Story cards also use \`legacy_featured_image\` or the first referenced photo where available. These changes repair **links and layout only**. They do not move photographs to the host or make absent files appear.

Original WordPress \`[gallery ids="..."]\` shortcodes, TravelPod and Flickr content may still need migration. Rebuilding WordPress galleries requires an attachment ID-to-file mapping from the old site/export and the actual photographs, not just the post HTML. The migration notes on affected articles are retained for review.

## Quality checks

On a build run:

```bash
hugo --gc --minify
python3 scripts/check_publication.py public
```

Pull requests run these checks without deploying. Merging to \`main\` deploys via \`.github/workflows/hugo.yml\`.

The existing \`scripts/audit_site.py\` inspects legacy image references, and can check responses for \`photos.offonourown.co.uk\` when run with network access.

## Audit a WordPress uploads ZIP

If you still have the old \`uploads.zip\` (~1.93 GB), keep it out of Git. On your Mac, place it alongside this repository and run:

```bash
python3 scripts/audit_media.py ./uploads.zip
```

This reads the ZIP file index without extracting the photographs. It compares image references in the migrated content with the archive and, if supplied, WordPress attachment records from \`migration/media-manifest.csv\`. Reports go into the \`media-audit/\` folder.

If you've extracted \`wp-content/uploads\`, you can pass that folder instead of the ZIP. The report does not upload images or change the deployed site.

## Safety

Do not commit full WordPress backups, raw exports, databases, contact submissions, credentials, or private drafts. Review imported content before publishing.
