-- Apply once, as schema owner, after schema.sql, seed.sql and portal_permissions.sql.
-- Forward validation only: historical results remain readable after a rule retires.
BEGIN;

CREATE FUNCTION guard_result_tree_insert() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE v_evaluation uuid;
BEGIN
  IF TG_TABLE_NAME = 'module_result' THEN
    v_evaluation := NEW.evaluation_id;
  ELSE
    SELECT evaluation_id INTO v_evaluation FROM module_result WHERE id = NEW.module_result_id;
  END IF;
  -- Decision INSERT takes the same parent lock, so finalization cannot race children.
  PERFORM id FROM evaluation WHERE id = v_evaluation FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Result tree requires an existing evaluation'; END IF;
  IF EXISTS (SELECT 1 FROM clinical_decision WHERE evaluation_id = v_evaluation) THEN
    RAISE EXCEPTION 'Evaluation result tree is finalized by its clinical decision';
  END IF;
  RETURN NEW;
END $$;
-- AFTER skips ON CONFLICT DO NOTHING replay; exceptions still roll back real inserts.
CREATE TRIGGER module_result_tree_guard AFTER INSERT ON module_result
  FOR EACH ROW EXECUTE FUNCTION guard_result_tree_insert();
CREATE TRIGGER recommendation_tree_guard AFTER INSERT ON recommendation
  FOR EACH ROW EXECUTE FUNCTION guard_result_tree_insert();
CREATE TRIGGER result_missing_field_tree_guard AFTER INSERT ON result_missing_field
  FOR EACH ROW EXECUTE FUNCTION guard_result_tree_insert();

CREATE FUNCTION lock_decision_result_tree() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  PERFORM id FROM evaluation WHERE id = NEW.evaluation_id FOR UPDATE;
  RETURN NEW;
END $$;
-- Runs alphabetically before the existing decision_validate trigger.
CREATE TRIGGER decision_result_tree_lock BEFORE INSERT ON clinical_decision
  FOR EACH ROW EXECUTE FUNCTION lock_decision_result_tree();

CREATE FUNCTION validate_module_result_integrity() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE v_mode text; v_rule rule_version;
BEGIN
  SELECT mode INTO v_mode FROM evaluation WHERE id = NEW.evaluation_id;
  IF v_mode = 'stub' THEN
    IF NEW.status <> 'mock_not_evaluated' OR NEW.rule_version_id IS NOT NULL THEN
      RAISE EXCEPTION 'Stub evaluation requires a mock result without a clinical rule';
    END IF;
  ELSIF v_mode = 'validated' THEN
    IF NEW.status = 'mock_not_evaluated' OR NEW.rule_version_id IS NULL THEN
      RAISE EXCEPTION 'Validated evaluation requires a non-mock result and an active approved rule';
    END IF;
    -- Share lock prevents retirement/content changes racing this result insert.
    SELECT * INTO v_rule FROM rule_version WHERE id = NEW.rule_version_id FOR SHARE;
    IF v_rule.id IS NULL OR v_rule.status <> 'active' OR v_rule.module <> NEW.module OR
       NOT EXISTS (SELECT 1 FROM rule_approval WHERE rule_version_id = v_rule.id
                   AND approved_content_hash = v_rule.content_hash) THEN
      RAISE EXCEPTION 'Result requires an active approved rule for the same module';
    END IF;
  ELSE
    RAISE EXCEPTION 'Result requires an existing evaluation';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER module_result_integrity BEFORE INSERT ON module_result
  FOR EACH ROW EXECUTE FUNCTION validate_module_result_integrity();

CREATE FUNCTION validate_recommendation_integrity() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM module_result r JOIN evaluation e ON e.id = r.evaluation_id
                 WHERE r.id = NEW.module_result_id AND r.status = 'completed' AND e.mode = 'validated') THEN
    RAISE EXCEPTION 'Recommendation requires a completed validated module result';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER recommendation_integrity BEFORE INSERT ON recommendation
  FOR EACH ROW EXECUTE FUNCTION validate_recommendation_integrity();

-- INSERT remains available before the decision, including in the creation transaction.
-- Every recorded row is final; corrections require a new evaluation.
CREATE TRIGGER module_result_immutable BEFORE UPDATE OR DELETE ON module_result
  FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
CREATE TRIGGER recommendation_immutable BEFORE UPDATE OR DELETE ON recommendation
  FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
CREATE TRIGGER result_missing_field_immutable BEFORE UPDATE OR DELETE ON result_missing_field
  FOR EACH ROW EXECUTE FUNCTION prevent_mutation();

COMMIT;
