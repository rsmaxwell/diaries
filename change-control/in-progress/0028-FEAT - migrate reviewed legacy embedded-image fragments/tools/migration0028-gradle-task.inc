// Explicit offline-only, reviewed 0028 data migration. Never wired into responder startup.
tasks.register('migration0028ReviewedFragments', JavaExec) {
    group = 'migration'
    description = 'Validate, dry-run, apply with explicit approval, or postflight reviewed legacy image Fragments.'
    dependsOn tasks.named('classes')
    classpath = sourceSets.main.runtimeClasspath
    mainClass = 'com.rsmaxwell.diaries.responder.migration.migration0028.Migration0028ReviewedFragments'
    doFirst {
        def mode = providers.gradleProperty('migrationMode').getOrElse('validate-manifest')
        def inputs = providers.gradleProperty('migrationManifest').orNull
        def output = providers.gradleProperty('migrationOutput').orNull
        def config = providers.gradleProperty('migrationConfig').orNull
        def plan = providers.gradleProperty('migrationPlan').orNull
        def approval = providers.gradleProperty('migrationApproval').orNull
        def production = providers.gradleProperty('migrationPermitProductionApply').orNull
        if (!(mode in ['analyse','validate-manifest','dry-run','apply','postflight']) || !inputs || !output)
            throw new GradleException('Requires -PmigrationManifest=<prepared-directory> -PmigrationOutput=<new-output> -PmigrationMode=<mode>')
        if (mode != 'validate-manifest' && !config)
            throw new GradleException('DB modes require -PmigrationConfig=<responder-json-config>')
        if (mode in ['postflight','apply'] && !plan)
            throw new GradleException('Apply/postflight require -PmigrationPlan=<reviewed-dry-run-plan>')
        if (mode == 'apply' && !approval)
            throw new GradleException('Apply requires -PmigrationApproval=<separately-approved-json>')
        args '--mode', mode, '--manifest', inputs, '--output', output
        if (config) args '--config', config
        if (plan) args '--plan', plan
        if (approval) args '--approval', approval
        if (production) args '--permit-production-apply', production
    }
}
