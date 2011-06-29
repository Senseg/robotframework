window.output = {};

function multiplyString(string, times) {
    var result = "";
    for (var i = 0; i < times; i++){
        result += string;
    }
    return result;
}

describe("Text decoder", function () {

    it("should have empty string with id 0", function () {
        window.output.strings = ["*"];
        var empty = store.get(0);
        expect(empty).toEqual("");
    });

    it("should uncompress", function () {
        window.output.strings = ["*", "eNorzk3MySmmLQEASKop9Q=="];
        var decompressed = store.get(1);
        var expected = multiplyString("small", 20);
        expect(decompressed).toEqual(expected);
    });

    it("should uncompress and replace compressed in memory", function () {
        window.output.strings = ["*", "eNorzk3MySmmLQEASKop9Q=="];
        expect(window.output.strings[1]).toEqual("eNorzk3MySmmLQEASKop9Q==");
        store.get(1);
        var expected = multiplyString("small", 20);
        expect(window.output.strings[1]).toEqual("*"+expected);
    });

    it("should handle plain text", function () {
        window.output.strings = ["*", "*plain text"];
        var actual = store.get(1);
        expect(actual).toEqual("plain text");
    });
});

function subSuite(index, suite) {
    if (!suite)
        suite = window.testdata.suite();
    return suite.suites()[index];
}

function firstTest(suite) {
    return suite.tests()[0];
}

function nthKeyword(item, n) {
    return item.keywords()[n];
}

describe("Handling Suite", function () {

    function getDate(offset) {
        return new Date(window.output.baseMillis + offset);
    }

    beforeEach(function () {
        window.output = window.suiteOutput;
    });

    function expectStats(suite, total, passed, critical, criticalPassed){
        expect(suite.total).toEqual(total);
        expect(suite.totalPassed).toEqual(passed);
        expect(suite.totalFailed).toEqual(total-passed);
        expect(suite.critical).toEqual(critical);
        expect(suite.criticalPassed).toEqual(criticalPassed);
        expect(suite.criticalFailed).toEqual(critical-criticalPassed);
    }

    function endsWith(string, ending) {
        var index = string.lastIndexOf(ending);
        return string.substring(index) == ending;
    }

    it("should parse suite", function () {
        var suite = window.testdata.suite();
        expect(suite.name).toEqual("Suite");
        expect(suite.status).toEqual("PASS");
        expect(endsWith(suite.source, "Suite.txt")).toEqual(true);
        expect(suite.doc()).toEqual("suite doc");
        expect(suite.times).toBeDefined();
        expect(suite.times.elapsedMillis).toBeGreaterThan(0);
        expect(suite.times.elapsedMillis).toBeLessThan(1000);
        expectStats(suite, 1, 1, 1, 1);
        expect(suite.metadata[0]).toEqual(["meta", "data"]);
    });

    it("should parse test", function () {
        var test = firstTest(window.testdata.suite());
        expect(test.name).toEqual("Test");
        expect(test.status).toEqual("PASS");
        expect(test.fullName).toEqual("Suite.Test");
        expect(test.doc()).toEqual("test doc");
        expect(test.tags).toEqual(["tag1", "tag2"]);
        expect(test.times).toBeDefined();
        expect(test.times.elapsedMillis).toBeGreaterThan(0);
        expect(test.times.elapsedMillis).toBeLessThan(window.testdata.suite().times.elapsedMillis+1);
        expect(test.timeout).toEqual("1 second");
    });

    it("should parse keyword", function () {
        var kw = nthKeyword(firstTest(window.testdata.suite()), 0);
        expect(kw.name).toEqual("BuiltIn.Log");
        expect(kw.status).toEqual("PASS");
        expect(kw.times).toBeDefined();
        expect(kw.times.elapsedMillis).toBeGreaterThan(0);
        expect(kw.times.elapsedMillis).toBeLessThan(firstTest(window.testdata.suite()).times.elapsedMillis+1);
        expect(kw.path).toEqual("Suite.Test.0");
        expect(kw.type).toEqual("KEYWORD");
    });

    it("should parse for loop", function() {
        var forloop = nthKeyword(firstTest(window.testdata.suite()), 1);
        expect(forloop.name).toEqual("${i} IN RANGE [ 2 ]");
        expect(forloop.type).toEqual("FOR");
        var foritem = nthKeyword(forloop, 0);
        expect(foritem.name).toEqual("${i} = 0");
        expect(foritem.type).toEqual("VAR");
        foritem = nthKeyword(forloop, 1);
        expect(foritem.name).toEqual("${i} = 1");
        expect(foritem.type).toEqual("VAR");
    });

    it("should parse message", function () {
        var message = nthKeyword(firstTest(window.testdata.suite()), 0).messages()[0];
        expect(message.text).toEqual("message");
        expect(message.time).toBeLessThan(new Date());
    });

    it("should parse timestamp", function () {
        var timestamp = window.testdata.generated();
        expect(timestamp).toEqual(new Date(window.output.baseMillis+window.output.generatedMillis));
    });

});

describe("Setups and teardowns", function () {

    beforeEach(function () {
        window.output = window.setupsAndTeardownsOutput;
    });

    function checkTypeNameArgs(kw, type, name, args) {
    	expect(kw.type).toEqual(type);
    	expect(kw.name).toEqual(name);
    	expect(kw.arguments).toEqual(args);
    }

    it("should parse suite setup", function () {
    	var suite = window.testdata.suite();
    	checkTypeNameArgs(suite.keywords()[0], "SETUP", "BuiltIn.Log", "suite setup");
    });

    it("should parse suite teardown", function () {
    	var suite = window.testdata.suite();
    	checkTypeNameArgs(suite.keywords()[1], "TEARDOWN", "BuiltIn.Log", "suite teardown");
    });

    it("should give navigation uniqueId list for a suite teardown keyword", function (){
        var uniqueIds = window.testdata.pathToKeyword("SetupsAndTeardowns.1");
        expect(uniqueIds[0]).toEqual(window.testdata.suite().id);
        expect(uniqueIds[1]).toEqual(nthKeyword(window.testdata.suite(), 1).id);
        expect(uniqueIds.length).toEqual(2);
    });

    it("should parse test setup", function () {
        checkTypeNameArgs(nthKeyword(firstTest(window.testdata.suite()), 0), "SETUP", "BuiltIn.Log", "test setup");
    });

    it("should parse test teardown", function () {
    	var test = firstTest(window.testdata.suite());
    	checkTypeNameArgs(nthKeyword(test, 2), "TEARDOWN", "BuiltIn.Log", "test teardown");
    });

    it("should give suite children in order", function () {
        var suite = window.testdata.suite();
        var children = suite.children();
        expect(children[0]).toEqual(nthKeyword(suite, 0));
        expect(children[1]).toEqual(nthKeyword(suite, 1));
        expect(children[2]).toEqual(firstTest(suite));
    });

    it("should give test children in order", function () {
        var test = firstTest(window.testdata.suite());
        var children = test.children();
        checkTypeNameArgs(children[0], "SETUP", "BuiltIn.Log", "test setup");
        checkTypeNameArgs(children[1], "KEYWORD", "Keyword with teardown", "");
        checkTypeNameArgs(children[2], "TEARDOWN", "BuiltIn.Log", "test teardown");
    });

    it("should parse keyword teardown", function () {
        var test = firstTest(window.testdata.suite());
        var children = test.children();
        checkTypeNameArgs(children[1].children()[1], "TEARDOWN", "BuiltIn.Log", "keyword teardown");
    });
});


describe("Short time formatting", function (){

    it("should pad 0 values to full length", function () {
        expect(window.model.shortTime(0,0,0,0)).toEqual("00:00:00.000");
    });

    it("should pad non empty number to full length", function () {
        expect(window.model.shortTime(12,5,55,101)).toEqual("12:05:55.101");
    });
});


describe("Handling messages", function (){

    beforeEach(function (){
        window.output = window.messagesOutput;
    });

    function expectMessage(message, txt, level) {
        expect(message.text).toEqual(txt);
        expect(message.level).toEqual(level);
    }

    function kwMessages(kw) {
        return nthKeyword(firstTest(window.testdata.suite()), kw).messages();
    }

    function kwMessage(kw) {
        return kwMessages(kw)[0];
    }

    it("should handle info level message", function () {
        expectMessage(kwMessage(1), "infolevelmessage", "info");
    });

    it("should handle warn level message", function () {
        expectMessage(kwMessage(2), "warning", "warn");
    });

    it("should handle debug level message", function () {
        var messages = kwMessages(4);
        expectMessage(messages[messages.length-2], "debugging", "debug");
    });

    it("should handle trace level message", function () {
        var messages = kwMessages(5);
        expectMessage(messages[messages.length-2], "tracing", "trace");
    });

    it("should handle html level message", function () {
        expectMessage(kwMessage(0), "<h1>html</h1>", "info");
    });

    it("should show warning in errors", function () {
        var firstError = window.testdata.errors().next()
        expectMessage(firstError, "warning", "warn");
        var pathToKeyword = window.testdata.pathToKeyword(firstError.link.substr(8));
        var errorKw = window.testdata.find(pathToKeyword[pathToKeyword.length-1]);
        expect(errorKw.messages()[0].level).toEqual("warn");
    });
});


describe("Parent Suite Teardown Failure", function (){
    beforeEach(function (){
        window.output = window.teardownFailureOutput;
    });

    it("should show test status as failed", function (){
        var test = firstTest(window.testdata.suite().suites()[0]);
        expect(test.status).toEqual("FAIL");
    });

    it("should show suite status as failed", function (){
        var suite = window.testdata.suite().suites()[0];
        expect(suite.status).toEqual("FAIL");
    });

    it("should show test message 'Teardown of the parent suite failed.'", function (){
        var test = firstTest(window.testdata.suite().suites()[0]);
        expect(test.message()).toEqual("Teardown of the parent suite failed.");
    });

    it("should show suite message 'Teardown of the parent suite failed.'", function (){
        var suite = window.testdata.suite().suites()[0];
        expect(suite.message()).toEqual("Teardown of the parent suite failed.");
    });

    it("should show root suite message 'Suite teardown failed:\nAssertionError'", function (){
        var root = window.testdata.suite();
        expect(root.message()).toEqual("Suite teardown failed:\nAssertionError");
    });

});

describe("Parent Suite Teardown and Test failure", function(){
    beforeEach(function (){
        window.output = window.teardownFailureOutput;
    });

    it("should show test message 'In test\n\nAlso teardown of the parent suite failed.'", function (){
        var test = window.testdata.suite().suites()[0].tests()[1];
        expect(test.message()).toEqual("In test\n\nAlso teardown of the parent suite failed.");
    });
})

describe("Test failure message", function (){

    beforeEach(function () {
        window.output = window.passingFailingOutput;
    });

    it("should show test failure message ''", function (){
        var test = window.testdata.suite().tests()[1];
        expect(test.message()).toEqual("In test");
    });
});

describe("Iterating Keywords", function (){

    beforeEach(function (){
        window.output = window.testsAndKeywordsOutput;
    });

    function test(){
        return firstTest(window.testdata.suite());
    }

    function kw(index){
        return test().keyword(index);
    }

    it("should give correct number of keywords", function () {
        expect(test().keywords().length).toEqual(4);
        expect(nthKeyword(test(), 0).keywords().length).toEqual(1);
        expect(nthKeyword(nthKeyword(test(), 0), 0).keywords().length).toEqual(0);
    });

    it("should be possible to go through all the keywords in order", function () {
        var expectedKeywords = ["kw1", "kw2", "kw3", "kw4"];
        for(var i = 0; i < test().numberOfKeywords; i++){
            expect(kw(i).name).toEqual(expectedKeywords[i]);
        }
    });

    it("should give keyword children in order", function () {
        var keyword = nthKeyword(firstTest(window.testdata.suite()), 0);
        var children = keyword.children();
        expect(children[0]).toEqual(nthKeyword(keyword, 0));
    });
});


describe("Iterating Tests", function (){

    beforeEach(function (){
        window.output = window.testsAndKeywordsOutput;
    });

    it("should give correct number of tests", function (){
        expect(window.testdata.suite().tests().length).toEqual(4);
    });

    it("should be possible to go through all the tests in order", function () {
        var expectedTests = ["Test 1", "Test 2", "Test 3", "Test 4"];
        var tests = window.testdata.suite().tests();
        for(var i = 0; i <tests.length ; i++){
            expect(tests[i].name).toEqual(expectedTests[i]);
        }
    });
});


describe("Iterating Suites", function () {

    beforeEach(function (){
        window.output = window.allDataOutput;
    });

    it("should give correct number of suites", function (){
        var suite = window.testdata.suite();
        var subSuites = suite.suites();
        expect(subSuites.length).toEqual(5);
        expect(subSuites[0].suites().length).toEqual(0);
        expect(subSuites[3].suites().length).toEqual(1);
    });

    it("should be possible to iterate suites", function (){
        var tests = 0;
        var subSuites = window.testdata.suite().suites();
        for(var i = 0 in subSuites){
            for(var j in subSuites[i].suites()){
                var testsuite = subSuites[i].suites()[j];
                tests += testsuite.tests().length;
                expect(testsuite.tests().length).toBeGreaterThan(0);
            }
        }
        expect(tests).toEqual(2);
    });

    it("should show correct full names", function (){
        var root = window.testdata.suite();
        expect(root.fullName).toEqual("Data");
        expect(root.suites()[0].fullName).toEqual("Data.Messages");
        expect(root.suites()[3].suites()[0].fullName).toEqual("Data.teardownFailure.PassingFailing");
        expect(root.suites()[3].suites()[0].tests()[0].fullName).toEqual("Data.teardownFailure.PassingFailing.Passing");
    });

    it("should give navigation uniqueId list for a test", function (){
        var uniqueIdList = window.testdata.pathToTest("Data.teardownFailure.PassingFailing.Passing");
        var root = window.testdata.suite();
        expect(uniqueIdList[0]).toEqual(root.id);
        expect(uniqueIdList[1]).toEqual(subSuite(3).id);
        expect(uniqueIdList[2]).toEqual(subSuite(3).suites()[0].id);
        expect(uniqueIdList[3]).toEqual(subSuite(3).suites()[0].tests()[0].id);
        expect(uniqueIdList.length).toEqual(4);
    });

    it("should give navigation uniqueId list for a keyword", function (){
        var uniqueIdList = window.testdata.pathToKeyword("Data.teardownFailure.PassingFailing.Passing.0");
        var root = window.testdata.suite();
        expect(uniqueIdList[0]).toEqual(root.id);
        expect(uniqueIdList[1]).toEqual(subSuite(3).id);
        expect(uniqueIdList[2]).toEqual(subSuite(3).suites()[0].id);
        expect(uniqueIdList[3]).toEqual(subSuite(3).suites()[0].tests()[0].id);
        expect(uniqueIdList[4]).toEqual(subSuite(3).suites()[0].tests()[0].keywords()[0].id);
        expect(uniqueIdList.length).toEqual(5);
    });

    it("should give navigation uniqueId list for a suite", function (){
        var uniqueIdList = window.testdata.pathToSuite("Data.teardownFailure.PassingFailing");
        var root = window.testdata.suite();
        expect(uniqueIdList[0]).toEqual(root.id);
        expect(uniqueIdList[1]).toEqual(root.suites()[3].id);
        expect(uniqueIdList[2]).toEqual(root.suites()[3].suites()[0].id);
        expect(uniqueIdList.length).toEqual(3);
    });

    it("should give navigation uniqueId list for the root suite", function (){
        var uniqueIdList = window.testdata.pathToSuite("Data");
        var root = window.testdata.suite();
        expect(uniqueIdList[0]).toEqual(root.id);
        expect(uniqueIdList.length).toEqual(1);
    });

    it("should give empty navigation uniqueId list for unknown element", function (){
        var uniqueIdList = window.testdata.pathToSuite("unknown");
        expect(uniqueIdList).toEqual([]);
    });
});

describe("Element ids", function (){

    beforeEach(function (){
        window.output = window.allDataOutput;
    });

    it("should give id for the main suite", function (){
        var suite = window.testdata.suite();
        expect(window.testdata.find(suite.id)).toEqual(suite);
    });

    it("should give id for a test", function (){
        var test = subSuite(0, subSuite(3)).tests()[0];
        expect(window.testdata.find(test.id)).toEqual(test);
    });

    it("should give id for a subsuite", function (){
        var subsuite = subSuite(3);
        expect(window.testdata.find(subsuite.id)).toEqual(subsuite);
    });

    it("should give id for a keyword", function (){
        var kw = subSuite(0, subSuite(3)).tests()[0].keywords()[0];
        expect(window.testdata.find(kw.id)).toEqual(kw);
    });

    it("should give id for a message", function (){
        var msg = subSuite(0, subSuite(3)).tests()[0].keywords()[0].messages()[0];
        expect(window.testdata.find(msg.id)).toEqual(msg);
    });

    it("should find right elements with right ids", function (){
        var suite = subSuite(3);
        var kw = subSuite(0, suite).tests()[0].keywords()[0];
        expect(kw.id).not.toEqual(suite.id);
        expect(window.testdata.find(kw.id)).toEqual(kw);
        expect(window.testdata.find(suite.id)).toEqual(suite);
    });
});

describe("Elements are created only once", function (){

    beforeEach(function (){
        window.output = window.passingFailingOutput;
    });

    it("should create suite only once", function (){
        var main1 = window.testdata.suite();
        var main2 = window.testdata.suite();
        expect(main1).not.toBeUndefined();
        expect(main1).toEqual(main2);
    });

    it("should create same test only once", function (){
        var test1 = window.testdata.suite().tests()[1];
        var test2 = window.testdata.suite().tests()[1];
        expect(test1).not.toBeUndefined();
        expect(test1).toEqual(test2);
    });

    it("should create same keyword only once", function (){
        var kw1 = window.testdata.suite().tests()[0].keywords()[0];
        var kw2 = window.testdata.suite().tests()[0].keywords()[0];
        expect(kw1).not.toBeUndefined();
        expect(kw1).toEqual(kw2);
    });
});

