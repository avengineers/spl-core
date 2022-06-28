properties([
   buildDiscarder(logRotator(numToKeepStr: '20')),
   disableConcurrentBuilds()
])

node('spl') {
    ws('spl') {
        init()
        test()
    }
}

def init() {
    checkout scm
}

def test() {
    stage('test') {
        try {
            bat '''
call spl.bat --installMandatory || exit /b 1
call spl.bat --build --target selftests || exit /b 1
'''
        } catch (e) {
            echo 'One or more selftests failed.'
        }
        
        junit allowEmptyResults: false, keepLongStdio: false, testResults: 'test/output/test-report.xml'
        junit allowEmptyResults: false, keepLongStdio: false, testResults: 'build/**/junit.xml'
        dir('build'){
            archiveArtifacts '**/coverage/*'
        }
    }
}
